"""
This module provides a client interface for interacting with a Milvus collection specifically designed to handle
document embeddings. It includes methods for connecting to a Milvus server, creating a collection with the appropriate
schema, inserting data, deleting documents, and managing indices.

Author: Anton Pastoriza
"""
import time
from logging import Logger
from typing import Optional

from pymilvus import connections, FieldSchema, DataType, CollectionSchema, Collection, MilvusException, Index, SearchResult, Hits, Hit
import numpy as np
from pymilvus.exceptions import DataNotMatchException
from pymilvus.orm.mutation import MutationResult

from embeddings.oai.composite_key_helper import generate_composite_key
from embeddings.oai.oai_embeddings_service import OAIEmbeddingsService
from utils import logging_config


class MilvusClient:
    """
    MilvusClient is responsible for managing the connection to a Milvus collection, specifically designed to handle
    document embeddings. It allows for inserting, deleting, and updating documents, as well as managing the collection's schema and index.

    Attributes:
        host (str): The host address of the Milvus server.
        port (str): The port of the Milvus server.
        logger (Logger): Logger instance for logging operations and errors.
        oai_embeddings_service (OAIEmbeddingsService): A service to generate embeddings
        collection (Collection): The Milvus collection instance for storing document embeddings.
    """

    def __init__(self, host: str = "milvus", port: str = "19530"):
        """
        Initializes the MilvusClient, connects to the Milvus server, and sets up the collection and index.

        Args:
            host (str): The host address of the Milvus server. Defaults to "milvus".
            port (str): The port of the Milvus server. Defaults to "19530".

        Raises:
            MilvusException: If connection to Milvus fails or if index creation fails.

        Notes:
            Break down of the index_params dictionary in detail to understand the meaning and implications
            of each component when creating an index in Milvus:

            1. IVF_FLAT - Inverted File (IVF) Index with Flat Quantization: This is one of the simplest
            and most commonly used index types in Milvus. It divides the vector space into multiple clusters
            (based on nlist), and within each cluster, vectors are stored as is (hence "flat").
            It is easy to implement and generally fast with good accuracy for many applications but may be
            memory-intensive because it doesn't compress the vectors within each cluster.

            2. nlist stands for the number of clusters or partitions that the IVF index will divide the
            vector space into. This parameter is crucial because it determines how the vectors are grouped
            and searched. The higher the number of clusters, the more accurate searches at the cost of performance

            3. metric_type defines the distance metric that Milvus will use to determine how "similar" or "close" two vectors are.
            L2 (Euclidean Distance) is the straight-line distance between two points in Euclidean space.
            It is calculated as the square root of the sum of the squared differences between corresponding coordinates of the vectors.

        """
        self.port = port
        self.host = host
        self.logger: Logger = logging_config.get_logger(__name__)
        self.oai_embeddings_service: OAIEmbeddingsService = OAIEmbeddingsService()
        self.collection: Optional[Collection] = None
        self._connect()

    def _connect(self, retries: int = 15, delay: int = 2):
        total_retries: int = 0
        got_response: bool = False
        while not got_response and total_retries < retries:
            try:
                connections.connect("default", host=self.host, port=self.port)
                # Define schema
                # For openai embedding, the length of the embedding vector will be
                # - 1536 for text-embedding-3-small
                # - 3072 for text-embedding-3-large
                fields = [
                    FieldSchema(name="composite_id", dtype=DataType.INT64, is_primary=True),  # Composite ID as the primary key
                    FieldSchema(name="doc_id", dtype=DataType.INT64),  # Document ID
                    FieldSchema(name="page_num", dtype=DataType.INT64),  # Page number
                    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=3072),  # text-embedding-3-small dimensions
                    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=32768)
                ]
                schema = CollectionSchema(fields, description="Financial plans embeddings collection")

                # Create collection
                self.collection = Collection("pdf_embeddings", schema)

                # Define the index parameters
                index_params = {
                    "index_type": "IVF_FLAT",
                    "params": {
                        "nlist": 128
                    },
                    "metric_type": "L2"
                }

                # Create the index on the embedding field
                index: Index = Index(self.collection, "embedding", index_params)

                self.logger.info("Milvus connection established at '%s'(%s) with index %s", self.host, self.port, index.index_name)
                got_response = True
            except MilvusException as e:
                self.logger.error("Failed to connect at '%s'(%s): %s", self.host, self.port, e)

            total_retries += 1
            if not got_response and total_retries < retries - 1:
                self.logger.info("Retrying Milvus connection at '%s' in %d seconds...", self.host, delay)
                time.sleep(delay)

    def delete_document_from_milvus(self, doc_id: int) -> int:
        """
        Deletes a document from the Milvus collection based on a single doc_id.

        Args:
            doc_id (int): The ID of the document to be deleted.

        Returns:
            int: The number of deleted records.

        Raises:
            MilvusException, DataNotMatchException: If the deletion fails.
        """
        expr = f"doc_id == {doc_id}"
        delete_count: int = self._delete_collection_from_milvus(expr)
        return delete_count

    def delete_documents_from_milvus(self, doc_ids: list[int]):
        """
        Deletes multiple documents from the Milvus collection based on a list of doc_ids.

        Args:
            doc_ids (list[int]): A list of document IDs to be deleted.

        Returns:
            int: The total number of deleted records.

        Raises:
            MilvusException, DataNotMatchException: If the deletion fails.
        """
        delete_count: int = 0
        if len(doc_ids) == 1:
            delete_count = self.delete_document_from_milvus(doc_ids[0])
        else:
            doc_ids_str: str = ', '.join(map(str, doc_ids))
            delete_expr: str = f"doc_id IN ({doc_ids_str})"
            delete_count = self._delete_collection_from_milvus(delete_expr)
        return delete_count

    def update_documents_from_milvus(self, doc_data: list[dict]):
        """
        Updates documents in the Milvus collection by first deleting any existing entries with the same doc_id
        and then inserting the new data.

        Args:
            doc_data (list[dict]): A list of dictionaries containing document data with keys "doc_id", "page_num", "embedding", and "text".

        Raises:
            MilvusException, DataNotMatchException: If the insertion fails.
        """
        # Delete any previous doc
        ids: list[int] = self._retrieve_ids(doc_data)
        if len(ids) > 0:
            self.delete_documents_from_milvus(ids)

        # Prepare documents insertion
        data_to_insert = [
            [generate_composite_key(item["doc_id"], item["page_num"]) for item in doc_data],
            [item["doc_id"] for item in doc_data],  # Document IDs
            [item["page_num"] for item in doc_data],  # Page numbers
            [np.array(item["embedding"], dtype=np.float32) for item in doc_data],  # Embeddings
            [item["text"] for item in doc_data]  # Text content
        ]

        try:
            # Insert data into the collection
            self.collection.insert(data_to_insert)
            self.collection.load()  # Prepare collection for searching
        except (MilvusException, DataNotMatchException) as e:
            self.logger.error("Failed to insert values values in Milvus: %s", e)

    def search(self, query: str, top_k: int = 5) -> list[str]:
        """
        Perform a vector similarity search in the Milvus collection using the provided query.

        This function generates an embedding for the given query, performs a similarity search
        in the Milvus collection using the L2 distance metric, and returns the top `top_k` results.
        If logging is set to DEBUG level, it logs detailed information about the results.

        Args:
            query (str): The input query string for which to search similar vectors.
            top_k (int): The number of top results to return. Defaults to 5.
                        Must be a positive integer.

        Returns:
            list: A list texts with the search results, or an empty list
                  if no results are found or if an error occurs.

        Raises:
            None: Any exceptions encountered during the search process are caught and logged, and an
                  empty list is returned.
        """
        search_results: list[str] = []
        query_embedding: list[float] = self.oai_embeddings_service.get_embeddings(query)
        search_params = {
            "metric_type": "L2",
            "params": {
                "nprobe": 10
            }
        }

        try:
            search_result: SearchResult = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=None,
                output_fields=["doc_id", "page_num", "text"]
            )
            for hits in search_result:
                for hit in hits:
                    self.logger.debug("Entity type: %s", type(hit))
                    self.logger.debug("Entity: %s", hit)
                    search_results.append(hit.get("text"))
        except MilvusException as e:
            self.logger.error("An error occurred during the search: %s", e)

        return search_results

    def _delete_collection_from_milvus(self, delete_expr: str) -> int:
        """
        Helper method that performs the delete operation in Milvus based on a delete expression and returns
        the count of deleted records.

        Args:
            delete_expr (str): The expression used to filter documents to delete.

        Returns:
            int: The number of deleted records.

        Raises:
            MilvusException, DataNotMatchException: If the deletion fails.
        """
        delete_count: int = 0
        try:
            # Perform the delete operation
            result: MutationResult = self.collection.delete(expr=delete_expr)
            delete_count = result.delete_count
            # Reload to refresh the in-memory data
            self.collection.load()
        except (MilvusException, DataNotMatchException) as e:
            self.logger.error("Failed to delete values in Milvus for expr '%s': %s", delete_expr, e)

        self.logger.debug("Deleted %d records for expr '%s'", delete_count, delete_expr)
        return delete_count

    def _retrieve_ids(self, doc_data: list[dict]) -> list[int]:
        """
        Helper method that retrieves (by generating) a list of composite doc_ids from
        the provided document data.

        Args:
            doc_data (list[dict]): A list of dictionaries containing document data.

        Returns:
            list[int]: A list of composite doc_ids generated from the document data.
        """
        doc_ids: set = {generate_composite_key(item["doc_id"], item["page_num"]) for item in doc_data}  # Composite ID
        self.logger.debug("Retrieved IDs: %s", doc_ids)
        return list(doc_ids)
