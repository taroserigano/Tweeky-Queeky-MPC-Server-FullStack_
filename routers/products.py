from fastapi import APIRouter, Depends, HTTPException, status, Query
from models.product import Product, Review
from models.user import User
from schemas.product import (
    ProductCreate, ProductUpdate, ReviewCreate,
    ProductResponse, ProductListResponse, ReviewResponse
)
from middleware.auth import get_current_user, require_admin
from config.settings import settings
from typing import Optional, List
from bson import ObjectId
from datetime import datetime
import math
import secrets

router = APIRouter(prefix="/api/products", tags=["products"])


def generate_sku_fallback() -> str:
    """Generate a SKU when no ObjectId-based SKU is available yet."""
    return f"SKU-{secrets.token_hex(4).upper()}"


def product_to_response(product: Product) -> ProductResponse:
    """Helper function to convert Product model to ProductResponse"""
    sku = product.sku or f"SKU-{str(product.id).upper()}"
    
    # Handle reviews - check if they're fetched (have attributes) or just Links
    reviews = []
    if product.reviews:
        for review in product.reviews:
            # Check if review is fetched (has attributes) or is a Link object
            if hasattr(review, 'name'):
                reviews.append(ReviewResponse(
                    _id=str(review.id),
                    name=review.name,
                    rating=review.rating,
                    comment=review.comment,
                    user=str(review.user),
                    createdAt=review.created_at
                ))
    
    return ProductResponse(
        _id=str(product.id),
        user=str(product.user),
        sku=sku,
        name=product.name,
        image=product.image,
        brand=product.brand,
        category=product.category,
        description=product.description,
        detailedDescription=product.detailed_description,
        specifications=product.specifications,
        reviews=reviews,
        rating=product.rating,
        numReviews=product.num_reviews,
        price=product.price,
        countInStock=product.count_in_stock,
        createdAt=product.created_at,
        updatedAt=product.updated_at
    )


@router.get("/top")
async def get_top_products():
    """Get featured products for carousel"""
    # Specific featured products for carousel (consumer products only)
    featured_names = [
        "Apple AirPods 4",
        "DYU 14 Folding Electric Bike",
        "BOSSIN Home Office Chair",
        "Shure SM7B"
    ]
    
    products = []
    for name in featured_names:
        product = await Product.find_one(
            {"name": {"$regex": name, "$options": "i"}},
            fetch_links=True
        )
        if product:
            products.append(product)
    
    # If featured products not found, fall back to top rated
    # Exclude recording equipment from top products
    if len(products) < 3:
        all_products = await Product.find(fetch_links=True).sort("-rating").to_list()
        # Filter out recording equipment categories
        filtered_products = [
            p for p in all_products 
            if p.category and p.category.lower() not in [
                'recording equipment',
                'audio interface',
                'studio equipment',
                'recording gear'
            ]
        ]
        products = filtered_products[:4]
    
    return [product_to_response(product) for product in products]


@router.get("/autocomplete")
async def get_autocomplete_suggestions(
    q: str = Query(..., min_length=1, max_length=100)
) -> List[dict]:
    """Get autocomplete suggestions for search query"""
    if len(q) < 2:
        return []
    
    # Search in product names, brands, and categories
    products = await Product.find({
        "$or": [
            {"name": {"$regex": q, "$options": "i"}},
            {"brand": {"$regex": q, "$options": "i"}},
            {"category": {"$regex": q, "$options": "i"}}
        ]
    }).limit(10).to_list()
    
    suggestions = []
    seen = set()
    
    for product in products:
        # Add product name
        if product.name not in seen:
            suggestions.append({
                "text": product.name,
                "type": "product",
                "id": str(product.id)
            })
            seen.add(product.name)
        
        # Add brand
        if product.brand and product.brand not in seen:
            suggestions.append({
                "text": product.brand,
                "type": "brand"
            })
            seen.add(product.brand)
        
        # Add category
        if product.category and product.category not in seen:
            suggestions.append({
                "text": product.category,
                "type": "category"
            })
            seen.add(product.category)
    
    return suggestions[:10]


@router.get("", response_model=ProductListResponse, response_model_exclude_none=False)
async def get_products(
    keyword: Optional[str] = None,
    page_number: int = Query(1, alias="pageNumber", ge=1),
    sort_by: Optional[str] = Query(None, alias="sortBy")
):
    """Fetch all products with pagination, search, and sorting
    
    Sort options:
    - price_asc: Price (Low to High)
    - price_desc: Price (High to Low)
    - rating_desc: Rating (High to Low)
    - newest: Newest First
    - oldest: Oldest First
    """
    page_size = settings.PAGINATION_LIMIT
    skip = page_size * (page_number - 1)
    
    query = {}
    if keyword:
        query = {"name": {"$regex": keyword, "$options": "i"}}
    
    # Build query
    query_builder = Product.find(query, fetch_links=True)
    
    # Apply sorting using Beanie syntax
    if sort_by == "price_asc":
        query_builder = query_builder.sort(+Product.price)
    elif sort_by == "price_desc":
        query_builder = query_builder.sort(-Product.price)
    elif sort_by == "rating_desc":
        query_builder = query_builder.sort(-Product.rating)
    elif sort_by == "oldest":
        query_builder = query_builder.sort(+Product.created_at)
    else:  # "newest" or default
        query_builder = query_builder.sort(-Product.created_at)
    
    count = await Product.find(query).count()
    products = await query_builder.skip(skip).limit(page_size).to_list()
    
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
    if product_data is None:
        product_data = ProductCreate()
    
    product = Product(
        name=product_data.name,
        price=product_data.price,
        user=current_user.id,
        sku=product_data.sku or generate_sku_fallback(),
        image=product_data.image,
        brand=product_data.brand,
        category=product_data.category,
        count_in_stock=product_data.count_in_stock,
        num_reviews=0,
        description=product_data.description,
        detailed_description=product_data.detailed_description,
        specifications=product_data.specifications,
    )
    
    await product.save()

    # If SKU was auto-generated, upgrade it to include the product id (stable + unique)
    if product.sku and product.sku.startswith("SKU-") and len(product.sku) == len("SKU-") + 8:
        product.sku = f"{product.sku}-{str(product.id)[-6:].upper()}"
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
    if product_data.sku is not None:
        product.sku = product_data.sku
    if product_data.price is not None:
        product.price = product_data.price
    if product_data.description:
        product.description = product_data.description
    if product_data.detailed_description is not None:
        product.detailed_description = product_data.detailed_description
    if product_data.specifications is not None:
        product.specifications = product_data.specifications
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
    
    if product.reviews is None:
        product.reviews = []
    
    already_reviewed = any(
        str(review.user) == str(current_user.id) 
        for review in product.reviews
    )
    
    if already_reviewed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product already reviewed"
        )
    
    review = Review(
        name=current_user.name,
        rating=review_data.rating,
        comment=review_data.comment,
        user=current_user.id
    )
    
    await review.insert()
    
    product_with_links = await Product.get(ObjectId(product_id))
    
    new_reviews_list = []
    
    if product_with_links.reviews:
        for existing_link in product_with_links.reviews:
            new_reviews_list.append(existing_link)
    
    new_reviews_list.append(review)
    
    product_with_links.reviews = new_reviews_list
    
    product_with_links.num_reviews = len(new_reviews_list)
    
    product_fetched = await Product.get(ObjectId(product_id), fetch_links=True)
    if product_fetched.reviews:
        total_rating = sum(r.rating for r in product_fetched.reviews)
        total_rating += review.rating
        product_with_links.rating = total_rating / (len(product_fetched.reviews) + 1)
    
    await product_with_links.save(link_rule="WRITE")
    
    return {"message": "Review added"}
