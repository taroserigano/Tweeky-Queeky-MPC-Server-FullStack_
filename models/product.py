from beanie import Document, PydanticObjectId, Link
from pydantic import Field, ConfigDict
from datetime import datetime
from typing import List, Optional


class Review(Document):
    name: str
    rating: int = Field(ge=1, le=5)
    comment: str
    user: PydanticObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True)

    class Settings:
        name = "reviews"


class Product(Document):
    user: PydanticObjectId
    name: str
    image: str
    brand: str
    category: str
    description: str
    reviews: List[Link[Review]] = Field(default_factory=list)
    rating: float = Field(default=0, ge=0, le=5)
    num_reviews: int = Field(default=0, alias="numReviews")
    price: float = Field(ge=0)
    count_in_stock: int = Field(default=0, alias="countInStock")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "name": "Sample Product",
                "image": "/images/sample.jpg",
                "brand": "Sample Brand",
                "category": "Electronics",
                "description": "Sample description",
                "price": 99.99,
                "countInStock": 10
            }
        }
    )

    class Settings:
        name = "products"
        use_state_management = True

    async def save(self, *args, **kwargs):
        """Update timestamp on save"""
        self.updated_at = datetime.utcnow()
        return await super().save(*args, **kwargs)
