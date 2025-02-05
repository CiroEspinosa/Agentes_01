import time
from logging import Logger
from typing import List
from pinecone import Pinecone, ServerlessSpec
from embeddings.oai.oai_embeddings_service import OAIEmbeddingsService
from utils import logging_config


class PineconeClient:
    """
    PineconeClient manages connection to a Pinecone index designed for document embeddings.
    It allows for inserting, deleting, updating documents, and searching similar embeddings.

    Attributes:
        api_key (str): Pinecone API key for authentication.
        region (str): Cloud region (e.g., 'us-west1-gcp').
        namespace (str): Name of the logical partition within the index # TODO: add a default, probably 'DataX'
        index_name (str): The name of the Pinecone index. # I Added the default value as seen in multi_agents branch, not sure if necessary
        logger (Logger): Logger instance for logging operations and errors.
        oai_embeddings_service (OAIEmbeddingsService): A service to generate embeddings.
    """

    def __init__(self, api_key: str, region: str, namespace:str, index_name: str = 'default_content_index', cloud: str = 'aws'):
        """
        Initializes the PineconeClient, connects to the Pinecone service, and sets up the index.

        Args:
            api_key (str): The API key for Pinecone.
            cloud (str): Cloud provider where the index will be hosted.
            region (str): Region where the index will be hosted.
            index_name (str): The name of the index.
        """
        self.api_key = api_key
        self.cloud = cloud
        self.region = region
        self.index_name = index_name
        self.logger: Logger = logging_config.get_logger(__name__)
        self.oai_embeddings_service: OAIEmbeddingsService = OAIEmbeddingsService()
        self.namespace: str = namespace

        # Initialize the Pinecone client
        self.pc = Pinecone(api_key=self.api_key)

        embedding_dimension = 1536

        index_names = [index.name for index in self.pc.list_indexes()]
        if self.index_name not in index_names:
            self.pc.create_index(
                name=self.index_name,
                dimension=embedding_dimension,
                metric="euclidean",
                spec=ServerlessSpec(
                    cloud=self.cloud,
                    region=self.region
                )
            )
            while True:
                index_description = self.pc.describe_index(self.index_name)
                if index_description.status == 'Ready':
                    break
                self.logger.debug("Waiting for index to be ready...")
                time.sleep(1)

        self.index = self.pc.Index(self.index_name)
        self.logger.info(f"Connected to Pinecone index '{self.index_name}'.")

    def search(self, query: str, top_k: int = 20) -> List[str]:
        """
        Perform a vector similarity search in Pinecone using the provided query.

        Args:
            query (str): Input string for similarity search.
            top_k (int): The number of top results to return.

        Returns:
            List[str]: Text content from the top search results.
        """

        query_embedding = self.oai_embeddings_service.get_embeddings(query[-6:]) # Habría que ajustar el valor de -6, no estamos comprobando el impacto, solo que funcione
        
        try:
            results = self.index.query(
                namespace=self.namespace,
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )

            return [match['metadata']['text'] for match in results.matches]
        except Exception as e:
            self.logger.error("Search failed in Pinecone: %s", e)
            return []
