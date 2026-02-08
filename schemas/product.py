from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime


# Request schemas
class ProductCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    sku: Optional[str] = None
    name: str = "Sample name"
    price: float = 0
    image: str = "/images/sample.png"
    brand: str = "Sample brand"
    category: str = "Sample category"
    count_in_stock: int = Field(0, alias="countInStock")
    description: str = "Sample description"
    detailed_description: Optional[str] = Field(None, alias="detailedDescription")
    specifications: Optional[Dict[str, Any]] = None


class ProductUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    sku: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    detailed_description: Optional[str] = Field(None, alias="detailedDescription")
    specifications: Optional[Dict[str, Any]] = None
    image: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    count_in_stock: Optional[int] = Field(None, alias="countInStock")


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str


# Response schemas
class ReviewResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    
    id: str = Field(alias="_id")
    name: str
    rating: int
    comment: str
    user: str
    created_at: datetime = Field(alias="createdAt")


class ProductResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    
    id: str = Field(alias="_id")
    user: str
    sku: Optional[str] = None
    name: str
    image: str
    brand: str
    category: str
    description: str
    detailed_description: Optional[str] = Field(None, alias="detailedDescription")
    specifications: Optional[Dict[str, Any]] = None
    reviews: List[ReviewResponse] = Field(default_factory=list)
    rating: float
    num_reviews: int = Field(alias="numReviews")
    price: float
    count_in_stock: int = Field(alias="countInStock")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class ProductListResponse(BaseModel):
    products: List[ProductResponse]
    page: int
    pages: int
