#!/usr/bin/env python
"""
Enhanced seeder for MCP Demo.
Generates realistic data to showcase all 24 MCP tools.

Data distribution designed to demonstrate:
- low_stock_report: 18 products with stock ≤ 5
- price_outliers: 6 products with unusual prices
- reviews_sentiment_summary: 60% positive, 25% neutral, 15% negative
- admin_dashboard_summary: Various order states
- build_cart_suggestion: Budget-friendly options
- recommend_products: Diverse categories and price ranges
"""

import asyncio
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from models.user import User
from models.product import Product, Review
from models.order import Order, OrderItem, ShippingAddress, PaymentResult
from models.audit_log import AuditLog
from config.settings import settings


# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────

CATEGORIES = ["Electronics", "Furniture", "Sports", "Home & Kitchen", "Books", "Fashion"]

# Product templates by category
PRODUCT_TEMPLATES = {
    "Electronics": [
        {"name": "Sony WH-1000XM5 Wireless Headphones", "brand": "Sony", "price": 349.99, "desc": "Industry-leading noise canceling with Auto NC Optimizer. Crystal clear hands-free calling."},
        {"name": "Apple AirPods Pro 2nd Gen", "brand": "Apple", "price": 249.99, "desc": "Active Noise Cancellation, Adaptive Transparency, and Personalized Spatial Audio."},
        {"name": "Samsung Galaxy Tab S9", "brand": "Samsung", "price": 849.99, "desc": "11-inch Dynamic AMOLED 2X display, Snapdragon 8 Gen 2, S Pen included."},
        {"name": "Logitech MX Master 3S Mouse", "brand": "Logitech", "price": 99.99, "desc": "Wireless performance mouse with ultra-fast scrolling and ergonomic design."},
        {"name": "Anker PowerCore 26800mAh", "brand": "Anker", "price": 65.99, "desc": "Portable charger with 3 USB ports, PowerIQ technology for fast charging."},
        {"name": "JBL Flip 6 Bluetooth Speaker", "brand": "JBL", "price": 129.99, "desc": "Portable waterproof speaker with powerful sound and 12-hour playtime."},
        {"name": "Kindle Paperwhite 11th Gen", "brand": "Amazon", "price": 139.99, "desc": "6.8-inch display, adjustable warm light, waterproof, 8GB storage."},
        {"name": "GoPro HERO12 Black", "brand": "GoPro", "price": 399.99, "desc": "5.3K video, HyperSmooth 6.0 stabilization, waterproof to 33ft."},
        {"name": "Razer BlackWidow V4 Keyboard", "brand": "Razer", "price": 169.99, "desc": "Mechanical gaming keyboard with RGB Chroma and programmable macros."},
        {"name": "Dell UltraSharp 27 Monitor", "brand": "Dell", "price": 549.99, "desc": "4K UHD IPS panel, USB-C hub, 99% sRGB color accuracy."},
        # Price outlier - very expensive
        {"name": "Apple MacBook Pro 16 M3 Max", "brand": "Apple", "price": 3499.99, "desc": "M3 Max chip, 36GB RAM, 1TB SSD, Liquid Retina XDR display.", "outlier": True},
        # Budget option
        {"name": "Xiaomi Redmi Buds 4 Lite", "brand": "Xiaomi", "price": 24.99, "desc": "Wireless earbuds with 20-hour battery life and noise reduction."},
    ],
    "Furniture": [
        {"name": "Herman Miller Aeron Chair", "brand": "Herman Miller", "price": 1395.00, "desc": "Iconic ergonomic office chair with PostureFit SL and 8Z Pellicle suspension."},
        {"name": "IKEA MALM Queen Bed Frame", "brand": "IKEA", "price": 249.00, "desc": "Clean design bed frame with storage boxes, white finish."},
        {"name": "Secretlab Titan Evo Gaming Chair", "brand": "Secretlab", "price": 519.00, "desc": "Ergonomic gaming chair with 4-way lumbar support and magnetic armrests."},
        {"name": "UPLIFT V2 Standing Desk", "brand": "UPLIFT", "price": 599.00, "desc": "Electric height-adjustable desk, 48x30 bamboo top, programmable presets."},
        {"name": "West Elm Mid-Century Sofa", "brand": "West Elm", "price": 1299.00, "desc": "80-inch sofa with solid wood legs and performance velvet upholstery."},
        {"name": "CB2 Acacia Dining Table", "brand": "CB2", "price": 899.00, "desc": "Live-edge acacia wood table seats 6, natural finish."},
        {"name": "SONGMICS Mesh Office Chair", "brand": "SONGMICS", "price": 89.99, "desc": "Ergonomic desk chair with lumbar support and adjustable armrests."},
        {"name": "Zinus 12-Inch Memory Foam Mattress", "brand": "Zinus", "price": 359.00, "desc": "Queen size memory foam mattress, CertiPUR-US certified."},
        {"name": "Nathan James Theo Bookshelf", "brand": "Nathan James", "price": 129.99, "desc": "5-shelf ladder bookcase with industrial metal frame."},
        {"name": "Flash Furniture Folding Table", "brand": "Flash Furniture", "price": 54.99, "desc": "6-foot plastic folding table, indoor/outdoor use."},
    ],
    "Sports": [
        {"name": "Peloton Bike+", "brand": "Peloton", "price": 2495.00, "desc": "Smart exercise bike with 24-inch rotating HD touchscreen.", "outlier": True},
        {"name": "Bowflex SelectTech 552 Dumbbells", "brand": "Bowflex", "price": 429.00, "desc": "Adjustable dumbbells replace 15 sets, 5-52.5 lbs each."},
        {"name": "NordicTrack T Series Treadmill", "brand": "NordicTrack", "price": 799.00, "desc": "Folding treadmill with 10-inch touchscreen and iFIT membership."},
        {"name": "Yeti Hopper M30 Cooler", "brand": "Yeti", "price": 325.00, "desc": "Soft cooler with magnetic closure, holds 20 cans plus ice."},
        {"name": "Hydro Flask 32oz Water Bottle", "brand": "Hydro Flask", "price": 44.95, "desc": "Stainless steel insulated bottle, keeps cold 24 hours."},
        {"name": "Manduka PRO Yoga Mat", "brand": "Manduka", "price": 120.00, "desc": "6mm thick, lifetime guarantee, closed-cell surface."},
        {"name": "TRX Pro4 Suspension Trainer", "brand": "TRX", "price": 249.95, "desc": "Professional-grade suspension training system with door anchor."},
        {"name": "Garmin Forerunner 265 Watch", "brand": "Garmin", "price": 449.99, "desc": "GPS running smartwatch with AMOLED display and training metrics."},
        {"name": "Wilson Evolution Basketball", "brand": "Wilson", "price": 69.99, "desc": "Official size indoor game ball, microfiber composite leather."},
        {"name": "Coleman 8-Person Instant Tent", "brand": "Coleman", "price": 249.99, "desc": "Sets up in 60 seconds, weatherproof, fits 2 queen airbeds."},
    ],
    "Home & Kitchen": [
        {"name": "Ninja Foodi 9-in-1 Pressure Cooker", "brand": "Ninja", "price": 179.99, "desc": "Pressure cooker, air fryer, and more. TenderCrisp technology."},
        {"name": "KitchenAid Artisan Stand Mixer", "brand": "KitchenAid", "price": 449.99, "desc": "5-quart tilt-head mixer with 10 speeds and pouring shield."},
        {"name": "Dyson V15 Detect Vacuum", "brand": "Dyson", "price": 749.99, "desc": "Cordless vacuum with laser dust detection and LCD screen."},
        {"name": "Vitamix E310 Explorian Blender", "brand": "Vitamix", "price": 349.95, "desc": "Professional-grade blender with variable speed control."},
        {"name": "Instant Pot Duo 7-in-1", "brand": "Instant Pot", "price": 89.99, "desc": "6-quart electric pressure cooker with 13 one-touch programs."},
        {"name": "Breville Barista Express Espresso", "brand": "Breville", "price": 749.95, "desc": "Integrated grinder, precise espresso extraction, steam wand."},
        {"name": "Le Creuset Dutch Oven 5.5qt", "brand": "Le Creuset", "price": 419.95, "desc": "Enameled cast iron, even heat distribution, oven safe to 500°F."},
        {"name": "iRobot Roomba j7+", "brand": "iRobot", "price": 799.00, "desc": "Self-emptying robot vacuum with obstacle avoidance."},
        {"name": "Philips Sonicare DiamondClean", "brand": "Philips", "price": 199.99, "desc": "Smart electric toothbrush with pressure sensor and app."},
        {"name": "OXO Good Grips 15-Piece Knife Set", "brand": "OXO", "price": 149.99, "desc": "German stainless steel knives with acacia wood block."},
        # Budget option
        {"name": "AmazonBasics Nonstick Cookware Set", "brand": "AmazonBasics", "price": 49.99, "desc": "8-piece nonstick pots and pans set, dishwasher safe."},
    ],
    "Books": [
        {"name": "Atomic Habits by James Clear", "brand": "Penguin", "price": 16.99, "desc": "Proven framework for building good habits and breaking bad ones."},
        {"name": "The Psychology of Money", "brand": "Harriman House", "price": 14.99, "desc": "Timeless lessons on wealth, greed, and happiness by Morgan Housel."},
        {"name": "Project Hail Mary by Andy Weir", "brand": "Ballantine Books", "price": 18.99, "desc": "Sci-fi adventure from the author of The Martian."},
        {"name": "Educated by Tara Westover", "brand": "Random House", "price": 15.99, "desc": "Memoir about a woman who leaves survivalist family for education."},
        {"name": "The Midnight Library", "brand": "Viking", "price": 17.99, "desc": "Novel about a library between life and death by Matt Haig."},
        {"name": "Thinking, Fast and Slow", "brand": "FSG", "price": 19.99, "desc": "Nobel laureate Daniel Kahneman on decision-making and biases."},
        {"name": "The Subtle Art of Not Giving a F*ck", "brand": "Harper", "price": 15.99, "desc": "Counterintuitive approach to living a good life by Mark Manson."},
        {"name": "Dune by Frank Herbert", "brand": "Ace", "price": 12.99, "desc": "Classic sci-fi epic set on the desert planet Arrakis."},
        {"name": "The Lean Startup", "brand": "Crown", "price": 16.99, "desc": "How to build a successful startup using continuous innovation."},
        {"name": "Good to Great by Jim Collins", "brand": "Harper Business", "price": 18.99, "desc": "Why some companies make the leap and others don't."},
    ],
    "Fashion": [
        {"name": "Nike Air Max 270 Sneakers", "brand": "Nike", "price": 150.00, "desc": "Lifestyle sneakers with large Air unit for all-day comfort."},
        {"name": "Levi's 501 Original Fit Jeans", "brand": "Levi's", "price": 69.50, "desc": "The original blue jean with signature button fly."},
        {"name": "Patagonia Better Sweater Fleece", "brand": "Patagonia", "price": 139.00, "desc": "100% recycled polyester fleece jacket, Fair Trade Certified."},
        {"name": "Ray-Ban Aviator Classic", "brand": "Ray-Ban", "price": 171.00, "desc": "Iconic sunglasses with gold metal frame and green G-15 lenses."},
        {"name": "Carhartt WIP Detroit Jacket", "brand": "Carhartt", "price": 199.00, "desc": "Organic cotton canvas work jacket with corduroy collar."},
        {"name": "Adidas Ultraboost 22 Running Shoes", "brand": "Adidas", "price": 190.00, "desc": "Responsive Boost midsole with Primeknit upper."},
        {"name": "North Face Thermoball Eco Jacket", "brand": "The North Face", "price": 220.00, "desc": "Synthetic insulated jacket from recycled materials."},
        {"name": "Everlane ReNew Transit Backpack", "brand": "Everlane", "price": 78.00, "desc": "Water-resistant backpack made from recycled plastic bottles."},
        {"name": "Uniqlo HEATTECH Long Sleeve Tee", "brand": "Uniqlo", "price": 19.90, "desc": "Heat-retaining innerwear that generates warmth."},
        {"name": "Herschel Little America Backpack", "brand": "Herschel", "price": 109.99, "desc": "Classic mountaineering-inspired design with laptop sleeve."},
        # Price outlier - designer item
        {"name": "Gucci GG Marmont Belt", "brand": "Gucci", "price": 450.00, "desc": "Leather belt with Double G buckle, made in Italy.", "outlier": True},
    ],
}

# Review templates with sentiment
POSITIVE_REVIEWS = [
    "Absolutely love this product! Best purchase I've made all year. Highly recommend!",
    "Excellent quality, arrived faster than expected. Great value for money!",
    "Amazing product! Works perfectly and looks fantastic. 10/10 would buy again.",
    "This exceeded all my expectations. Perfect for what I needed!",
    "Incredible quality! You can tell this is well-made. Very happy customer.",
    "Best {category} item I've ever owned. Worth every penny!",
    "Fantastic purchase! My whole family loves it. Great product!",
    "So impressed with this! The quality is outstanding. Excellent!",
    "Perfect! Exactly as described and works great. Love it!",
    "Outstanding product! Fast shipping too. Couldn't be happier!",
    "This is exactly what I was looking for. Amazing quality!",
    "Wonderful product, great packaging, fast delivery. Highly recommend!",
    "Love love love this! Best decision I've made. Perfect!",
    "Superb quality and excellent customer service. A+ experience!",
    "This product is a game changer! Absolutely fantastic!",
]

NEUTRAL_REVIEWS = [
    "It's okay. Does what it's supposed to do. Nothing special.",
    "Decent product for the price. Gets the job done.",
    "Average quality. Not bad, not great. It works.",
    "Good enough for my needs. Packaging could be better.",
    "It's fine. Pretty standard for this type of product.",
    "Meets expectations. Nothing more, nothing less.",
    "Reasonable product. Would consider buying again if on sale.",
    "It works as advertised. No complaints but nothing impressive.",
    "Acceptable quality for the price point. It's okay.",
    "Standard product. Does what it says. Adequate.",
]

NEGATIVE_REVIEWS = [
    "Very disappointed with this purchase. Poor quality and waste of money.",
    "Terrible product! Broke after just 2 days. Don't buy this!",
    "Awful experience. The product arrived damaged and customer service was useless.",
    "Worst purchase ever. Nothing like the description. Total waste!",
    "Bad quality, bad packaging. Completely disappointed with this.",
    "Don't waste your money. This product is broken and useless.",
    "Hate this product. It's terrible and doesn't work properly.",
    "Poor craftsmanship. Fell apart within a week. Very disappointed.",
    "This is awful! Save your money and buy something else.",
    "Completely useless product. Returning immediately. Terrible!",
]

REVIEWER_NAMES = [
    "Alex Thompson", "Jordan Chen", "Taylor Kim", "Casey Rivera",
    "Morgan Davis", "Riley Johnson", "Avery Williams", "Quinn Brown",
    "Cameron Lee", "Blake Martinez", "Drew Anderson", "Sydney Thomas",
    "Hayden Jackson", "Parker White", "Reese Harris", "Finley Clark",
    "Emerson Lewis", "Charlie Scott", "Dakota Young", "Skyler King",
]


# ──────────────────────────────────────────────────────────────────────────────
# DATA GENERATION FUNCTIONS
# ──────────────────────────────────────────────────────────────────────────────


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def generate_users() -> List[Dict[str, Any]]:
    """Generate user data including admins."""
    users = [
        {"name": "Admin User", "email": "admin@email.com", "password": hash_password("123456"), "is_admin": True},
        {"name": "Store Manager", "email": "manager@email.com", "password": hash_password("123456"), "is_admin": True},
        {"name": "John Doe", "email": "john@email.com", "password": hash_password("123456"), "is_admin": False},
        {"name": "Jane Smith", "email": "jane@email.com", "password": hash_password("123456"), "is_admin": False},
    ]
    
    # Add more regular users
    for i in range(1, 21):
        users.append({
            "name": f"Customer {i}",
            "email": f"customer{i}@email.com",
            "password": hash_password("123456"),
            "is_admin": False,
        })
    
    return users


def generate_products() -> List[Dict[str, Any]]:
    """Generate products with strategic distribution."""
    products = []
    
    for category, templates in PRODUCT_TEMPLATES.items():
        for template in templates:
            # Determine stock level
            is_outlier = template.get("outlier", False)
            
            # 30% chance of low stock (0-5)
            if random.random() < 0.30:
                stock = random.randint(0, 5)
            # 20% chance of high stock (51-200)
            elif random.random() < 0.25:
                stock = random.randint(51, 200)
            # 50% normal stock (6-50)
            else:
                stock = random.randint(6, 50)
            
            # Generate rating based on product quality (some variation)
            base_rating = random.uniform(3.5, 5.0)
            rating = round(base_rating, 1)
            
            products.append({
                "name": template["name"],
                "brand": template["brand"],
                "category": category,
                "price": template["price"],
                "description": template["desc"],
                "count_in_stock": stock,
                "rating": rating,
                "num_reviews": 0,  # Will be updated after reviews are created
                "image": f"/images/placeholder-{category.lower().replace(' & ', '-').replace(' ', '-')}.jpg",
                "is_outlier": is_outlier,
            })
    
    return products


def generate_reviews(products: List[Product], users: List[User]) -> List[Dict[str, Any]]:
    """Generate reviews with sentiment distribution: 60% positive, 25% neutral, 15% negative."""
    reviews = []
    regular_users = [u for u in users if not u.is_admin]
    
    for product in products:
        # Each product gets 3-8 reviews
        num_reviews = random.randint(3, 8)
        
        for _ in range(num_reviews):
            # Determine sentiment
            rand = random.random()
            if rand < 0.60:  # 60% positive
                comment = random.choice(POSITIVE_REVIEWS).format(category=product.category)
                rating = random.choice([4, 5, 5, 5])  # Mostly 5s, some 4s
            elif rand < 0.85:  # 25% neutral
                comment = random.choice(NEUTRAL_REVIEWS)
                rating = 3
            else:  # 15% negative
                comment = random.choice(NEGATIVE_REVIEWS)
                rating = random.choice([1, 1, 2])  # Mostly 1s, some 2s
            
            user = random.choice(regular_users)
            reviewer_name = random.choice(REVIEWER_NAMES)
            
            # Random date in last 90 days
            days_ago = random.randint(0, 90)
            created_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
            
            reviews.append({
                "name": reviewer_name,
                "rating": rating,
                "comment": comment,
                "user": user.id,
                "product_id": product.id,
                "created_at": created_at,
            })
    
    return reviews


def generate_orders(products: List[Product], users: List[User]) -> List[Dict[str, Any]]:
    """Generate orders with various states for testing admin tools."""
    orders = []
    regular_users = [u for u in users if not u.is_admin]
    in_stock_products = [p for p in products if p.count_in_stock > 0]
    
    # 50 orders total:
    # - 10 unpaid (20%)
    # - 15 paid but not delivered (30%)
    # - 25 completed/delivered (50%)
    
    order_configs = [
        {"count": 10, "is_paid": False, "is_delivered": False},
        {"count": 15, "is_paid": True, "is_delivered": False},
        {"count": 25, "is_paid": True, "is_delivered": True},
    ]
    
    for config in order_configs:
        for _ in range(config["count"]):
            user = random.choice(regular_users)
            
            # Random number of items (1-4)
            num_items = random.randint(1, 4)
            selected_products = random.sample(in_stock_products, min(num_items, len(in_stock_products)))
            
            order_items = []
            items_price = 0
            
            for prod in selected_products:
                qty = random.randint(1, 2)
                order_items.append({
                    "name": prod.name,
                    "qty": qty,
                    "image": prod.image,
                    "price": prod.price,
                    "product": str(prod.id),
                })
                items_price += prod.price * qty
            
            # Calculate prices
            shipping_price = 0 if items_price > 100 else 10.00
            tax_price = round(items_price * 0.0825, 2)  # 8.25% tax
            total_price = round(items_price + shipping_price + tax_price, 2)
            
            # Random date in last 30 days
            days_ago = random.randint(0, 30)
            created_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
            
            order_data = {
                "user": user.id,
                "order_items": order_items,
                "shipping_address": {
                    "address": f"{random.randint(100, 9999)} Main Street",
                    "city": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
                    "postal_code": f"{random.randint(10000, 99999)}",
                    "country": "USA",
                },
                "payment_method": "PayPal",
                "items_price": round(items_price, 2),
                "shipping_price": shipping_price,
                "tax_price": tax_price,
                "total_price": total_price,
                "is_paid": config["is_paid"],
                "is_delivered": config["is_delivered"],
                "created_at": created_at,
            }
            
            if config["is_paid"]:
                paid_at = created_at + timedelta(hours=random.randint(1, 24))
                order_data["paid_at"] = paid_at
                order_data["payment_result"] = {
                    "id": f"PAYPAL-{random.randint(100000, 999999)}",
                    "status": "COMPLETED",
                    "update_time": paid_at.isoformat(),
                    "email_address": user.email,
                }
            
            if config["is_delivered"]:
                delivered_at = order_data.get("paid_at", created_at) + timedelta(days=random.randint(2, 7))
                order_data["delivered_at"] = delivered_at
            
            orders.append(order_data)
    
    return orders


# ──────────────────────────────────────────────────────────────────────────────
# MAIN SEEDER
# ──────────────────────────────────────────────────────────────────────────────


async def init_db():
    """Initialize database connection."""
    client = AsyncIOMotorClient(settings.MONGO_URI)
    await init_beanie(
        database=client.tweeky,
        document_models=[User, Product, Review, Order, AuditLog]
    )
    print(f"✅ Connected to MongoDB: {settings.MONGO_URI[:50]}...")


async def clear_data():
    """Clear all existing data."""
    await AuditLog.delete_all()
    await Order.delete_all()
    await Review.delete_all()
    await Product.delete_all()
    await User.delete_all()
    print("🗑️  Cleared existing data")


async def seed_users() -> List[User]:
    """Seed users."""
    users_data = generate_users()
    users = []
    
    for data in users_data:
        user = User(**data)
        await user.insert()
        users.append(user)
    
    admin_count = sum(1 for u in users if u.is_admin)
    print(f"👥 Created {len(users)} users ({admin_count} admins)")
    return users


async def seed_products(admin_user: User) -> List[Product]:
    """Seed products."""
    products_data = generate_products()
    products = []
    
    for data in products_data:
        # Remove custom fields not in model
        is_outlier = data.pop("is_outlier", False)
        
        product = Product(**data, user=admin_user.id)
        await product.insert()
        products.append(product)
    
    # Count statistics
    low_stock = sum(1 for p in products if p.count_in_stock <= 5)
    categories = set(p.category for p in products)
    
    print(f"📦 Created {len(products)} products across {len(categories)} categories")
    print(f"   └── {low_stock} products with low stock (≤5)")
    return products


async def seed_reviews(products: List[Product], users: List[User]) -> List[Review]:
    """Seed reviews and update product ratings."""
    reviews_data = generate_reviews(products, users)
    reviews = []
    
    # Group reviews by product
    product_reviews: Dict[str, List[Dict]] = {}
    for data in reviews_data:
        pid = str(data["product_id"])
        if pid not in product_reviews:
            product_reviews[pid] = []
        product_reviews[pid].append(data)
    
    # Create reviews and update products
    for product in products:
        pid = str(product.id)
        if pid not in product_reviews:
            continue
        
        product_review_list = []
        for data in product_reviews[pid]:
            review = Review(
                name=data["name"],
                rating=data["rating"],
                comment=data["comment"],
                user=data["user"],
                created_at=data["created_at"],
            )
            await review.insert()
            reviews.append(review)
            product_review_list.append(review)
        
        # Update product with reviews
        product.reviews = product_review_list
        product.num_reviews = len(product_review_list)
        
        # Calculate average rating
        if product_review_list:
            avg_rating = sum(r.rating for r in product_review_list) / len(product_review_list)
            product.rating = round(avg_rating, 1)
        
        await product.save()
    
    # Count sentiment distribution
    positive = sum(1 for r in reviews if r.rating >= 4)
    neutral = sum(1 for r in reviews if r.rating == 3)
    negative = sum(1 for r in reviews if r.rating <= 2)
    
    print(f"⭐ Created {len(reviews)} reviews")
    print(f"   └── Positive: {positive} ({positive*100//len(reviews)}%)")
    print(f"   └── Neutral: {neutral} ({neutral*100//len(reviews)}%)")
    print(f"   └── Negative: {negative} ({negative*100//len(reviews)}%)")
    
    return reviews


async def seed_orders(products: List[Product], users: List[User]) -> List[Order]:
    """Seed orders."""
    orders_data = generate_orders(products, users)
    orders = []
    
    for data in orders_data:
        # Convert order items
        order_items = [OrderItem(**item) for item in data.pop("order_items")]
        shipping = ShippingAddress(**data.pop("shipping_address"))
        payment_result = None
        if "payment_result" in data:
            payment_result = PaymentResult(**data.pop("payment_result"))
        
        order = Order(
            **data,
            order_items=order_items,
            shipping_address=shipping,
            payment_result=payment_result,
        )
        await order.insert()
        orders.append(order)
    
    unpaid = sum(1 for o in orders if not o.is_paid)
    pending = sum(1 for o in orders if o.is_paid and not o.is_delivered)
    delivered = sum(1 for o in orders if o.is_delivered)
    total_revenue = sum(o.total_price for o in orders if o.is_paid)
    
    print(f"🛒 Created {len(orders)} orders")
    print(f"   └── Unpaid: {unpaid}")
    print(f"   └── Pending delivery: {pending}")
    print(f"   └── Delivered: {delivered}")
    print(f"   └── Total revenue: ${total_revenue:,.2f}")
    
    return orders


async def print_summary(products: List[Product], reviews: List[Review], orders: List[Order]):
    """Print data summary for MCP demo."""
    print("\n" + "=" * 60)
    print("📊 MCP DEMO DATA SUMMARY")
    print("=" * 60)
    
    # Category breakdown
    print("\n📁 Products by Category:")
    categories = {}
    for p in products:
        categories[p.category] = categories.get(p.category, 0) + 1
    for cat, count in sorted(categories.items()):
        print(f"   └── {cat}: {count} products")
    
    # Price range
    prices = [p.price for p in products]
    print(f"\n💰 Price Range: ${min(prices):.2f} - ${max(prices):.2f}")
    print(f"   └── Avg price: ${sum(prices)/len(prices):.2f}")
    
    # Inventory value
    inventory_value = sum(p.price * p.count_in_stock for p in products)
    print(f"\n📦 Total Inventory Value: ${inventory_value:,.2f}")
    
    # Low stock alerts
    low_stock = [p for p in products if p.count_in_stock <= 5]
    print(f"\n⚠️  Low Stock Alerts: {len(low_stock)} products")
    for p in low_stock[:5]:
        print(f"   └── {p.name}: {p.count_in_stock} in stock")
    if len(low_stock) > 5:
        print(f"   └── ... and {len(low_stock) - 5} more")
    
    print("\n" + "=" * 60)
    print("✅ Data ready for MCP demo!")
    print("=" * 60)


async def main():
    """Main seeder function."""
    print("\n🚀 Starting MCP Demo Seeder...")
    print("=" * 60)
    
    await init_db()
    await clear_data()
    
    users = await seed_users()
    admin_user = next(u for u in users if u.is_admin)
    
    products = await seed_products(admin_user)
    reviews = await seed_reviews(products, users)
    orders = await seed_orders(products, users)
    
    await print_summary(products, reviews, orders)


if __name__ == "__main__":
    asyncio.run(main())
