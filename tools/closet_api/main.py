import uvicorn
from fastapi import FastAPI

from factory import web_factory
from utils import logging_config
from logging import Logger

app: FastAPI = web_factory.create_app()

logger: Logger = logging_config.get_logger(__name__)

# Mock data for available clothes
clothes_closet = {
    "clothes": [
        {"item": "White dress shirt", "type": "shirt", "formal": True},
        {"item": "Black blazer", "type": "blazer", "formal": True},
        {"item": "Navy blue suit pants", "type": "pants", "formal": True},
        {"item": "Casual jeans", "type": "pants", "formal": False},
        {"item": "Red tie", "type": "tie", "formal": True},
        {"item": "Leather shoes", "type": "shoes", "formal": True},
        {"item": "Sneakers", "type": "shoes", "formal": False},
        {"item": "Black belt", "type": "accessory", "formal": True},
        {"item": "Formal watch", "type": "accessory", "formal": True},
    ]
}

@app.get(
    "/api/clothes",
    response_model=dict,
    summary="Get Available Clothes",
    description="This endpoint returns a list of all the clothes available in the closet, including information about their type and whether they are suitable for formal events.",
    tags=["Clothes Inventory"],
    responses={
        200: {
            "description": "A list of available clothes from the closet.",
            "content": {
                "application/json": {
                    "example": {
                        "clothes": [
                            {"item": "White dress shirt", "type": "shirt", "formal": True},
                            {"item": "Black blazer", "type": "blazer", "formal": True},
                            {"item": "Navy blue suit pants", "type": "pants", "formal": True},
                            {"item": "Casual jeans", "type": "pants", "formal": False},
                            {"item": "Red tie", "type": "tie", "formal": True},
                            {"item": "Leather shoes", "type": "shoes", "formal": True},
                            {"item": "Sneakers", "type": "shoes", "formal": False},
                            {"item": "Black belt", "type": "accessory", "formal": True},
                            {"item": "Formal watch", "type": "accessory", "formal": True}
                        ]
                    }
                }
            },
        },
        400: {"description": "Invalid request or parameters"},
        500: {"description": "Internal server error"},
    }
)
def get_clothes():
    return clothes_closet


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7120)