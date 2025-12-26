from fastapi import APIRouter, Depends, HTTPException, status, Query
from models.product import Product, Review
from models.user import User
from schemas.product import (
    ProductCreate, ProductUpdate, ReviewCreate,
    ProductResponse, ProductListResponse, ReviewResponse
)
from middleware.auth import get_current_user, require_admin
from config.settings import settings
from typing import Optional
from bson import ObjectId
from datetime import datetime
import math

router = APIRouter(prefix="/api/products", tags=["products"])


def product_to_response(product: Product) -> ProductResponse:
    """Helper function to convert Product model to ProductResponse"""
    return ProductResponse(
        _id=str(product.id),
        user=str(product.user),
        name=product.name,
        image=product.image,
        brand=product.brand,
        category=product.category,
        description=product.description,
        reviews=[
            ReviewResponse(
                _id=str(review.id),
                name=review.name,
                rating=review.rating,
                comment=review.comment,
                user=str(review.user),
                createdAt=review.created_at
            )
            for review in (product.reviews or [])
        ],
        rating=product.rating,
        numReviews=product.num_reviews,
        price=product.price,
        countInStock=product.count_in_stock,
        createdAt=product.created_at,
        updatedAt=product.updated_at
    )


@router.get("/top")
async def get_top_products():
    """Get top rated products"""
    products = await Product.find(fetch_links=True).sort("-rating").limit(3).to_list()
    
    return [product_to_response(product) for product in products]


@router.get("", response_model=ProductListResponse, response_model_exclude_none=False)
async def get_products(
    keyword: Optional[str] = None,
    page_number: int = Query(1, alias="pageNumber", ge=1)
):
    """Fetch all products with pagination and search"""
    page_size = settings.PAGINATION_LIMIT
    skip = page_size * (page_number - 1)
    
    # Build query
    query = {}
    if keyword:
        query = {"name": {"$regex": keyword, "$options": "i"}}
    
    # Get count and products
    count = await Product.find(query).count()
    products = await Product.find(query, fetch_links=True).skip(skip).limit(page_size).to_list()
    
    pages = math.ceil(count / page_size) if count > 0 else 1
    
    return ProductListResponse(
        products=[product_to_response(product) for product in products],
        page=page_number,
        pages=pages
    )


@router.get("/{product_id}", response_model=ProductResponse, response_model_exclude_none=False)
async def get_product_by_id(product_id: str):
    """Fetch single product"""
    try:
        product = await Product.get(ObjectId(product_id), fetch_links=True)
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product_to_response(product)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: Optional[ProductCreate] = None,
    current_user: User = Depends(require_admin)
):
    """Create a product (Admin only)"""
    # Use default values if no data provided
    if product_data is None:
        product_data = ProductCreate()
    
    product = Product(
        name=product_data.name,
        price=product_data.price,
        user=current_user.id,
        image=product_data.image,
        brand=product_data.brand,
        category=product_data.category,
        count_in_stock=product_data.count_in_stock,
        num_reviews=0,
        description=product_data.description
    )
    
    await product.save()
    
    return product_to_response(product)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    admin_user: User = Depends(require_admin)
):
    """Update a product (Admin only)"""
    try:
        product = await Product.get(ObjectId(product_id), fetch_links=True)
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if product_data.name:
        product.name = product_data.name
    if product_data.price is not None:
        product.price = product_data.price
    if product_data.description:
        product.description = product_data.description
    if product_data.image:
        product.image = product_data.image
    if product_data.brand:
        product.brand = product_data.brand
    if product_data.category:
        product.category = product_data.category
    if product_data.count_in_stock is not None:
        product.count_in_stock = product_data.count_in_stock
    
    await product.save()
    
    return product_to_response(product)


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    admin_user: User = Depends(require_admin)
):
    """Delete a product (Admin only)"""
    try:
        product = await Product.get(ObjectId(product_id), fetch_links=True)
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    await product.delete()
    
    return {"message": "Product removed"}


@router.post("/{product_id}/reviews", status_code=status.HTTP_201_CREATED)
async def create_product_review(
    product_id: str,
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_user)
):
    """Create new product review"""
    try:
        product = await Product.get(ObjectId(product_id), fetch_links=True)
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Ensure reviews list is initialized
    if product.reviews is None:
        product.reviews = []
    
    # Check if user already reviewed
    already_reviewed = any(
        str(review.user) == str(current_user.id) 
        for review in product.reviews
    )
    
    if already_reviewed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product already reviewed"
        )
    
    # Create review document
    review = Review(
        name=current_user.name,
        rating=review_data.rating,
        comment=review_data.comment,
        user=current_user.id
    )
    
    # Save review first - MUST save before linking
    await review.insert()
    
    # CRITICAL FIX: Refetch product WITHOUT fetch_links first to get Link objects
    product_with_links = await Product.get(ObjectId(product_id))
    
    # Build new reviews list preserving existing Link objects
    new_reviews_list = []
    
    # If product has existing reviews as Links, keep them as Links
    if product_with_links.reviews:
        for existing_link in product_with_links.reviews:
            new_reviews_list.append(existing_link)
    
    # Add the new review (Beanie will convert Review to Link automatically)
    new_reviews_list.append(review)
    
    # Assign the complete list
    product_with_links.reviews = new_reviews_list
    
    # Update review count and rating
    product_with_links.num_reviews = len(new_reviews_list)
    
    # Calculate average rating - need to fetch reviews for this
    product_fetched = await Product.get(ObjectId(product_id), fetch_links=True)
    if product_fetched.reviews:
        total_rating = sum(r.rating for r in product_fetched.reviews)
        # Add new review rating
        total_rating += review.rating
        product_with_links.rating = total_rating / (len(product_fetched.reviews) + 1)
    
    # Save with link_rule to write all links
    await product_with_links.save(link_rule="WRITE")
    
    return {"message": "Review added"}
