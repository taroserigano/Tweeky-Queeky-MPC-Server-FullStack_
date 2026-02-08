import asyncio
import sys
import random
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import bcrypt

from models.user import User
from models.product import Product, Review
from models.order import Order
from config.settings import settings


PLACEHOLDER_IMAGES = {"/images/sample.jpg", "/images/sample.jpeg", "/images/sample.png"}


def build_detailed_description(name: str, brand: str, category: str, short_description: str) -> str:
    """Generate an Amazon-like detailed description when none is provided."""
    clean_name = (name or "").strip() or "This item"
    clean_brand = (brand or "").strip()
    clean_category = (category or "").strip()
    clean_short = (short_description or "").strip()

    parts = []
    if clean_brand and clean_category:
        parts.append(f"{clean_name} by {clean_brand} is a {clean_category.lower()} product designed for everyday use.")
    elif clean_brand:
        parts.append(f"{clean_name} by {clean_brand} is designed for everyday use.")
    elif clean_category:
        parts.append(f"{clean_name} is a {clean_category.lower()} product designed for everyday use.")
    else:
        parts.append(f"{clean_name} is designed for everyday use.")

    if clean_short:
        parts.append(clean_short)

    parts.append(
        "Use it at home, at work, or on the go depending on your setup. "
        "If you need help choosing between similar options, ask for a comparison and I’ll line them up side by side."
    )

    return " ".join(p.strip().rstrip(".") + "." for p in parts if p and p.strip())


def normalize_seed_product(product_data: dict) -> dict:
    """Ensure seeded products have rich fields and consistent placeholder images."""
    image = product_data.get("image")
    if not image or image in {"/images/sample.jpg", "/images/sample.jpeg"}:
        product_data["image"] = "/images/sample.png"

    if not product_data.get("sku"):
        brand = (product_data.get("brand") or "").strip().upper()[:3] or "SKU"
        name = (product_data.get("name") or "").strip()
        digest = hashlib.sha1(f"{brand}|{name}".encode("utf-8")).hexdigest()[:10].upper()
        product_data["sku"] = f"{brand}-{digest}"

    if not product_data.get("detailed_description"):
        product_data["detailed_description"] = build_detailed_description(
            product_data.get("name", ""),
            product_data.get("brand", ""),
            product_data.get("category", ""),
            product_data.get("description", ""),
        )

    return product_data


# Hash passwords using bcrypt directly
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


# Sample review comments for generating reviews
REVIEW_COMMENTS = {
    5: [
        "Absolutely love this product! Exceeded all my expectations.",
        "Best purchase I've made in years. Highly recommend!",
        "Perfect quality and fast shipping. Will buy again!",
        "Amazing product! Worth every penny.",
        "Couldn't be happier with this purchase. 5 stars!",
    ],
    4: [
        "Great product, minor issues but overall very satisfied.",
        "Really good quality. Shipping was a bit slow though.",
        "Does exactly what it's supposed to. Very happy.",
        "Solid purchase. Would recommend to friends.",
        "Good value for the price. Works great!",
    ],
    3: [
        "Decent product. Gets the job done.",
        "Average quality, nothing special but not bad either.",
        "It's okay. Expected a bit more for the price.",
        "Works fine but has some room for improvement.",
        "Meets basic expectations. Nothing more.",
    ],
    2: [
        "Disappointed with the quality. Expected better.",
        "Not as described. Wouldn't recommend.",
        "Had some issues. Customer service was helpful though.",
    ],
    1: [
        "Poor quality. Broke after a week.",
        "Not worth the money. Very disappointed.",
    ]
}

REVIEWER_NAMES = [
    "Michael S.", "Sarah L.", "David K.", "Emily R.", "Chris M.",
    "Jessica T.", "Ryan P.", "Amanda B.", "Kevin H.", "Lisa N.",
    "James W.", "Rachel D.", "Daniel F.", "Nicole C.", "Andrew G.",
]


# Sample users
USERS = [
    {
        "name": "Admin User",
        "email": "admin@email.com",
        "password": hash_password("123456"),
        "is_admin": True
    },
    {
        "name": "John Doe",
        "email": "john@email.com",
        "password": hash_password("123456"),
        "is_admin": False
    },
    {
        "name": "Jane Doe",
        "email": "jane@email.com",
        "password": hash_password("123456"),
        "is_admin": False
    }
]

# Sample products with Amazon-like rich descriptions and specifications
PRODUCTS = [
    {
        "name": "Apple AirPods 4",
        "image": "/images/Apple-AirPods-4_970671e7-764d-4536-9f51-666941f35ad3.012d4c1b577966703dc4b6947a77677b.avif",
        "brand": "Apple",
        "category": "Electronics",
        "description": "Premium wireless earbuds with spatial audio",
        "detailed_description": "Experience superior sound quality with Apple AirPods 4. These wireless earbuds feature Personalized Spatial Audio with dynamic head tracking for an immersive listening experience. The new H2 chip delivers powerful performance and efficiency. Adaptive EQ automatically tunes music to your ears, while the longer battery life keeps you going all day. Sweat and water resistant (IPX4), perfect for workouts and outdoor activities. Force sensor lets you control your music and calls. Quick access to Siri with 'Hey Siri'. Automatic switching between Apple devices. Seamless setup and device connectivity with all your Apple devices.",
        "specifications": {
            "Weight": "4.3g per earbud",
            "Dimensions": "30.9 x 18.3 x 19.2mm per earbud",
            "Battery Life": "Up to 6 hours listening time, 30 hours with charging case",
            "Connectivity": "Bluetooth 5.3",
            "Water Resistance": "IPX4 (sweat and water resistant)",
            "Chip": "Apple H2",
            "Audio": "Personalized Spatial Audio, Adaptive EQ",
            "Microphones": "Dual beamforming microphones",
            "Sensors": "Dual optical sensors, Motion-detecting accelerometer, Speech-detecting accelerometer, Force sensor",
            "Case Dimensions": "50.8 x 50.8 x 21.2mm",
            "Case Weight": "38g"
        },
        "price": 179.99,
        "count_in_stock": 10,
        "rating": 4.6,
        "num_reviews": 12
    },
    {
        "name": "BOSSIN Home Office Chair",
        "image": "/images/BOSSIN-Home-Office-Chair-Adult-Leather-High-Back-Adjustable-with-Arms-and-Lumbar-Support-Pink_c2ae285f-055d-4b7d-b5c1-3a5cd089c0ff.db5e5b58f7627bfdd0e560d711f1282e.avif",
        "brand": "BOSSIN",
        "category": "Furniture",
        "description": "Ergonomic office chair with lumbar support",
        "detailed_description": "Upgrade your workspace with the BOSSIN Home Office Chair, designed for all-day comfort and productivity. Features premium PU leather upholstery that's both durable and easy to clean. The high-back design with integrated lumbar support promotes healthy posture during long work sessions. Adjustable height mechanism accommodates users of different heights. Padded armrests reduce shoulder and arm strain. Smooth-rolling casters allow easy movement across various floor types. The 360-degree swivel provides excellent mobility. Sturdy metal base supports up to 300 lbs. Assembly is quick and straightforward with included tools and clear instructions. Perfect for home offices, executive suites, or study areas.",
        "specifications": {
            "Dimensions": "25.5\"D x 25.5\"W x 46-50\"H",
            "Seat Height": "18-22 inches (adjustable)",
            "Seat Width": "20 inches",
            "Seat Depth": "19.5 inches",
            "Weight Capacity": "300 lbs",
            "Material": "PU Leather, High-density foam padding",
            "Base": "360-degree swivel, 5-star metal base",
            "Casters": "Smooth-rolling nylon casters",
            "Armrests": "Fixed, padded",
            "Back Type": "High back with lumbar support",
            "Color": "Pink",
            "Assembly": "Required (tools included)"
        },
        "price": 249.99,
        "count_in_stock": 7,
        "rating": 4.4,
        "num_reviews": 8
    },
    {
        "name": "DYU 14 Folding Electric Bike",
        "image": "/images/DYU-14-Folding-Electric-Bike-for-Adults-Teens-350W-36V-7-5AH-Pedal-Assist-Commuter-Cruiser-City-E-Bike_bcd35cdc-65ff-486b-abd1-908daaac7871.085ea88ceec9fe2467d1776a8.avif",
        "brand": "DYU",
        "category": "Sports",
        "description": "Folding electric bike for adults",
        "price": 599.99,
        "count_in_stock": 5,
        "rating": 4.3,
        "num_reviews": 3
    },
    {
        "name": "Focusrite Scarlett 2i2 4th Gen",
        "image": "/images/Focusrite-Scarlett-2i2-4th-Gen-USB-Audio-Interface-with-Hi-Z-Instrument_93631c3b-e9b8-45d7-9f2d-219a79591be3.968b73e11420b91fae88e621862d6004.avif",
        "brand": "Focusrite",
        "category": "Electronics",
        "description": "USB Audio Interface for recording",
        "detailed_description": "The Focusrite Scarlett 2i2 4th Generation is the world's best-selling USB audio interface, now even better. Featuring high-performance 4th generation preamps with the best-performing mic preamp the Scarlett range has ever seen. Air mode gives your recordings a brighter, more open sound. Two balanced line outputs connect to studio monitors. Auto Gain and Clip Safe features intelligently set your levels. USB-C connectivity provides bus power - no external power supply needed. Direct monitoring with no latency. Works with all major DAWs including Pro Tools, Ableton, Logic Pro, and more. Two combination inputs accept XLR, 1/4\" TRS, and Hi-Z instrument cables. Perfect for singer-songwriters, podcasters, and home studio producers.",
        "specifications": {
            "Inputs": "2x Combination XLR-1/4\" TRS",
            "Outputs": "2x 1/4\" TRS balanced line outputs",
            "Monitor Output": "1x 1/4\" TRS stereo output",
            "Preamps": "High-performance 4th gen Scarlett preamps",
            "Sample Rate": "Up to 192kHz/24-bit",
            "Dynamic Range": "120dB (A-D, D-A)",
            "Connectivity": "USB-C",
            "Power": "Bus-powered via USB",
            "Dimensions": "7.3 x 3.7 x 1.9 inches",
            "Weight": "1.3 lbs",
            "Phantom Power": "+48V switchable",
            "Air Mode": "Yes",
            "Direct Monitor": "Yes",
            "Software Included": "Pro Tools Artist, Ableton Live Lite, Plugin Collective"
        },
        "price": 189.99,
        "count_in_stock": 11,
        "rating": 4.7,
        "num_reviews": 15
    },
    {
        "name": "Ibanez Gio GRX70QA Electric Guitar",
        "image": "/images/Ibanez-Gio-GRX70QA-Electric-Guitar-Trans-Violet-Sunburst-853_6bc3c252-632f-4f5e-af9a-bb38e238c3fe.37fa073e3e42738a9019d7f4c2f5f2af.avif",
        "brand": "Ibanez",
        "category": "Music",
        "description": "Electric guitar with quilted maple art grain top",
        "price": 299.99,
        "count_in_stock": 6,
        "rating": 4.5,
        "num_reviews": 10
    },
    {
        "name": "Owala FreeSip Water Bottle 24oz",
        "image": "/images/Owala-FreeSip-Stainless-Steel-Water-Bottle-24oz-White_69369768-4981-497b-8eba-c02663e7c575.7acc737755cc5a214a1a0e7ca6d7ac0a.avif",
        "brand": "Owala",
        "category": "Home",
        "description": "Insulated stainless steel water bottle",
        "price": 32.99,
        "count_in_stock": 20,
        "rating": 4.9,
        "num_reviews": 25
    },
    # Products with remaining real images
    {
        "name": "Shure SM7B Dynamic Microphone",
        "image": "/images/Shure-SM7B-Microphone-Wired-Dynamic-Microphone-Player-Heart-shaped-Vocal-Dynamic-Suitable-for-Blogs-Broadcasts-Media-Entertainment-etc_40f5c2ec-e291-4008-bdb9-9c0904.avif",
        "brand": "Shure",
        "category": "Electronics",
        "description": "Professional dynamic microphone for podcasting and streaming",
        "detailed_description": "The legendary Shure SM7B is the choice of top podcasters, streamers, and recording artists worldwide. Its smooth, flat, wide-range frequency response delivers clean, warm vocals with exceptional clarity. Advanced electromagnetic shielding blocks interference from computer monitors and other studio equipment. The internal air suspension shock isolation virtually eliminates mechanical noise transmission. Bass rolloff and mid-range emphasis controls let you shape your sound. Includes switchable bass rolloff and presence boost. Improved rejection of electromagnetic hum. Classic cardioid pattern isolates your voice while rejecting background noise. Requires a high-gain preamp or cloudlifter for optimal performance. Built like a tank with legendary Shure durability. Professional-grade XLR connection. The go-to mic for Joe Rogan, podcast studios, and professional broadcasters.",
        "specifications": {
            "Type": "Dynamic microphone",
            "Polar Pattern": "Cardioid",
            "Frequency Response": "50Hz - 20kHz",
            "Output Impedance": "150 ohms",
            "Sensitivity": "-59 dBV/Pa (1.12 mV)",
            "Connector": "3-pin XLR",
            "Weight": "1.69 lbs (765g)",
            "Dimensions": "7.75 x 3.88 x 3.88 inches",
            "Switches": "Bass rolloff, Mid-range emphasis (presence boost)",
            "Mounting": "5/8\"-27 threaded swivel mount",
            "Hum Rejection": "Excellent electromagnetic shielding",
            "Color": "Black",
            "Cable": "Not included (requires XLR cable)",
            "Preamp Required": "High-gain preamp recommended (60+ dB gain)"
        },
        "price": 399.99,
        "count_in_stock": 8,
        "rating": 4.9,
        "num_reviews": 42
    },
    {
        "name": "Shure BETA 58A Vocal Microphone",
        "image": "/images/Shure-BETA-58A-Professional-Studio-Supercardioid-Dynamic-Vocal-Mic-Microphone_b40736cd-3acd-4f57-89ea-ac997653edc6_1.8a164b274165528acebeca94733b3c16.avif",
        "brand": "Shure",
        "category": "Electronics",
        "description": "Supercardioid dynamic vocal microphone for live performances",
        "price": 159.99,
        "count_in_stock": 12,
        "rating": 4.7,
        "num_reviews": 28
    },
    {
        "name": "Mini 4K Projector",
        "image": "/images/Projector-4K-1080P-Support-Mini-Projector-Smart-for-Movie-Projection-Compatible-with-Phone-White_751b3fa1-4766-40a5-b772-319e5c3bbba1.5d86888b3dd15bf3a786ea005bb1a0c.avif",
        "brand": "Generic",
        "category": "Electronics",
        "description": "4K 1080P support mini projector for home theater",
        "price": 129.99,
        "count_in_stock": 15,
        "rating": 4.2,
        "num_reviews": 36
    },
    {
        "name": "HP 67XL High Yield Black Ink",
        "image": "/images/HP-67XL-High-Yield-Black-Original-Ink-Cartridge-240-Pages-3YM57AN-140_2bf9a0f2-6972-4f8f-82bb-5d5e5db8d1a6.078a187a259ed5050859d50744b099ad.avif",
        "brand": "HP",
        "category": "Office",
        "description": "High yield black original ink cartridge, 240 pages",
        "price": 32.99,
        "count_in_stock": 50,
        "rating": 4.4,
        "num_reviews": 89
    },
    {
        "name": "MAINSTAYS 16oz Pint Glass Set",
        "image": "/images/MAINSTAYS-160-oz-Milk-Beer-Everyday-Clear-Pint-Glass_d3f64668-5683-454c-ac39-8649cafc0518.e4a9b94263082ec337331be055ffd5a8.avif",
        "brand": "Mainstays",
        "category": "Home",
        "description": "Clear everyday pint glass, perfect for milk or beer",
        "price": 8.99,
        "count_in_stock": 100,
        "rating": 4.1,
        "num_reviews": 156
    },
    # Products with placeholder images
    {
        "name": "Sony WH-1000XM5 Wireless Headphones",
        "image": "/images/sample.jpg",
        "brand": "Sony",
        "category": "Electronics",
        "description": "Industry-leading noise canceling with Auto NC Optimizer. Crystal clear hands-free calling.",
        "detailed_description": "Experience the pinnacle of wireless audio with Sony's WH-1000XM5 headphones. Industry-leading noise cancellation powered by two processors controlling 8 microphones blocks out the world so you can focus on your music. Auto NC Optimizer automatically optimizes noise canceling based on your wearing conditions and environment. Magnificent sound engineered to perfection with the new Integrated Processor V1 unlocking the full potential of Sony's HD Noise Canceling Processor QN1. Ultra-comfortable, lightweight design with soft-fit leather for all-day wear. Crystal-clear hands-free calling with 4 beamforming microphones and advanced audio signal processing. Up to 30 hours battery life with quick charging (3 min = 3 hours). Multipoint connection lets you pair with two devices at once. Speak-to-Chat automatically pauses music when you speak. Premium carrying case included.",
        "specifications": {
            "Type": "Closed, dynamic",
            "Driver Unit": "30mm dome type",
            "Frequency Response": "4Hz-40,000Hz",
            "Noise Cancellation": "Industry-leading with 8 microphones",
            "Battery Life": "Up to 30 hours (NC ON), 40 hours (NC OFF)",
            "Quick Charging": "3 min charge = 3 hours playback",
            "Charging Port": "USB Type-C",
            "Bluetooth": "5.2",
            "Codecs": "LDAC, AAC, SBC",
            "Weight": "8.8 oz (250g)",
            "Microphones": "4 beamforming mics + 4 NC mics",
            "Multipoint": "Connects to 2 devices simultaneously",
            "Controls": "Touch sensor, wear detection",
            "Foldable": "No (flat folding design)",
            "Included": "Carrying case, USB-C cable, audio cable"
        },
        "price": 349.99,
        "count_in_stock": 31,
        "rating": 4.8,
        "num_reviews": 7
    },
    {
        "name": "Apple AirPods Pro 2nd Gen",
        "image": "/images/airpods.jpg",
        "brand": "Apple",
        "category": "Electronics",
        "description": "Active Noise Cancellation, Adaptive Transparency, and Personalized Spatial Audio.",
        "price": 249.99,
        "count_in_stock": 24,
        "rating": 4.7,
        "num_reviews": 3
    },
    {
        "name": "Samsung Galaxy Tab S9",
        "image": "/images/sample.jpg",
        "brand": "Samsung",
        "category": "Electronics",
        "description": "11-inch Dynamic AMOLED 2X display, Snapdragon 8 Gen 2, S Pen included.",
        "price": 849.99,
        "count_in_stock": 18,
        "rating": 4.5,
        "num_reviews": 5
    },
    {
        "name": "Logitech MX Master 3S Mouse",
        "image": "/images/sample.jpg",
        "brand": "Logitech",
        "category": "Electronics",
        "description": "Wireless performance mouse with ultra-fast scrolling and ergonomic design.",
        "price": 99.99,
        "count_in_stock": 20,
        "rating": 4.6,
        "num_reviews": 8
    },
    {
        "name": "Anker PowerCore 26800mAh",
        "image": "/images/sample.jpg",
        "brand": "Anker",
        "category": "Electronics",
        "description": "Portable charger with 3 USB ports, PowerIQ technology for fast charging.",
        "price": 65.99,
        "count_in_stock": 35,
        "rating": 4.5,
        "num_reviews": 4
    },
    {
        "name": "JBL Flip 6 Bluetooth Speaker",
        "image": "/images/sample.jpg",
        "brand": "JBL",
        "category": "Electronics",
        "description": "Portable waterproof speaker with powerful sound and 12-hour playtime.",
        "price": 129.99,
        "count_in_stock": 13,
        "rating": 4.4,
        "num_reviews": 5
    },
    {
        "name": "Kindle Paperwhite 11th Gen",
        "image": "/images/sample.jpg",
        "brand": "Amazon",
        "category": "Electronics",
        "description": "6.8-inch display, adjustable warm light, waterproof, 8GB storage.",
        "price": 139.99,
        "count_in_stock": 68,
        "rating": 4.7,
        "num_reviews": 5
    },
    {
        "name": "GoPro HERO12 Black",
        "image": "/images/sample.jpg",
        "brand": "GoPro",
        "category": "Electronics",
        "description": "5.3K video, HyperSmooth 6.0 stabilization, waterproof to 33ft.",
        "price": 399.99,
        "count_in_stock": 9,
        "rating": 4.6,
        "num_reviews": 5
    },
    {
        "name": "Razer BlackWidow V4 Keyboard",
        "image": "/images/sample.jpg",
        "brand": "Razer",
        "category": "Electronics",
        "description": "Mechanical gaming keyboard with RGB Chroma and programmable macros.",
        "price": 169.99,
        "count_in_stock": 28,
        "rating": 4.5,
        "num_reviews": 3
    },
    {
        "name": "Dell UltraSharp 27 Monitor",
        "image": "/images/sample.jpg",
        "brand": "Dell",
        "category": "Electronics",
        "description": "4K UHD IPS panel, USB-C hub, 99% sRGB color accuracy.",
        "price": 549.99,
        "count_in_stock": 7,
        "rating": 4.6,
        "num_reviews": 6
    },
    {
        "name": "Apple MacBook Pro 16 M3 Max",
        "image": "/images/sample.jpg",
        "brand": "Apple",
        "category": "Electronics",
        "description": "M3 Max chip, 36GB RAM, 1TB SSD, Liquid Retina XDR display.",
        "price": 3499.99,
        "count_in_stock": 4,
        "rating": 4.9,
        "num_reviews": 7
    },
    {
        "name": "Nintendo Switch OLED",
        "image": "/images/sample.jpg",
        "brand": "Nintendo",
        "category": "Gaming",
        "description": "7-inch OLED screen, enhanced audio, 64GB internal storage.",
        "price": 349.99,
        "count_in_stock": 22,
        "rating": 4.8,
        "num_reviews": 15
    },
    {
        "name": "PlayStation 5 Console",
        "image": "/images/sample.jpg",
        "brand": "Sony",
        "category": "Gaming",
        "description": "Next-gen gaming with ultra-high speed SSD and ray tracing.",
        "price": 499.99,
        "count_in_stock": 5,
        "rating": 4.9,
        "num_reviews": 23
    },
    {
        "name": "Xbox Series X",
        "image": "/images/sample.jpg",
        "brand": "Microsoft",
        "category": "Gaming",
        "description": "12 teraflops of processing power, 4K gaming at 120fps.",
        "price": 499.99,
        "count_in_stock": 8,
        "rating": 4.8,
        "num_reviews": 19
    },
    {
        "name": "Dyson V15 Detect Vacuum",
        "image": "/images/sample.jpg",
        "brand": "Dyson",
        "category": "Home",
        "description": "Cordless vacuum with laser dust detection and LCD screen.",
        "price": 749.99,
        "count_in_stock": 6,
        "rating": 4.7,
        "num_reviews": 11
    },
    {
        "name": "Instant Pot Duo 7-in-1",
        "image": "/images/sample.jpg",
        "brand": "Instant Pot",
        "category": "Home",
        "description": "Electric pressure cooker, slow cooker, rice cooker, and more.",
        "price": 89.99,
        "count_in_stock": 40,
        "rating": 4.6,
        "num_reviews": 45
    },
    {
        "name": "Ninja Foodi Air Fryer",
        "image": "/images/sample.jpg",
        "brand": "Ninja",
        "category": "Home",
        "description": "6-quart air fryer with 4-in-1 functionality.",
        "price": 159.99,
        "count_in_stock": 25,
        "rating": 4.5,
        "num_reviews": 32
    },
    {
        "name": "KitchenAid Stand Mixer",
        "image": "/images/sample.jpg",
        "brand": "KitchenAid",
        "category": "Home",
        "description": "5-quart stainless steel bowl, 10 speeds, tilt-head design.",
        "price": 379.99,
        "count_in_stock": 12,
        "rating": 4.8,
        "num_reviews": 28
    },
    {
        "name": "Philips Sonicare Toothbrush",
        "image": "/images/sample.jpg",
        "brand": "Philips",
        "category": "Personal Care",
        "description": "Electric toothbrush with pressure sensor and smart timer.",
        "price": 149.99,
        "count_in_stock": 30,
        "rating": 4.6,
        "num_reviews": 18
    },
    {
        "name": "Fitbit Charge 6",
        "image": "/images/sample.jpg",
        "brand": "Fitbit",
        "category": "Wearables",
        "description": "Advanced fitness tracker with GPS and heart rate monitoring.",
        "price": 159.99,
        "count_in_stock": 20,
        "rating": 4.4,
        "num_reviews": 14
    },
    {
        "name": "Apple Watch Series 9",
        "image": "/images/sample.jpg",
        "brand": "Apple",
        "category": "Wearables",
        "description": "Always-on Retina display, S9 chip, Double Tap gesture.",
        "price": 399.99,
        "count_in_stock": 15,
        "rating": 4.8,
        "num_reviews": 21
    },
    {
        "name": "Samsung Galaxy Watch 6",
        "image": "/images/sample.jpg",
        "brand": "Samsung",
        "category": "Wearables",
        "description": "Advanced sleep coaching, body composition analysis.",
        "price": 299.99,
        "count_in_stock": 18,
        "rating": 4.5,
        "num_reviews": 12
    },
    {
        "name": "Bose QuietComfort Ultra",
        "image": "/images/sample.jpg",
        "brand": "Bose",
        "category": "Electronics",
        "description": "Wireless noise cancelling headphones with spatial audio.",
        "price": 429.99,
        "count_in_stock": 10,
        "rating": 4.7,
        "num_reviews": 9
    },
    {
        "name": "Canon EOS R6 Mark II",
        "image": "/images/sample.jpg",
        "brand": "Canon",
        "category": "Electronics",
        "description": "Full-frame mirrorless camera with 24.2MP sensor and 4K video.",
        "price": 2499.99,
        "count_in_stock": 3,
        "rating": 4.9,
        "num_reviews": 6
    },
    {
        "name": "DJI Mini 4 Pro Drone",
        "image": "/images/sample.jpg",
        "brand": "DJI",
        "category": "Electronics",
        "description": "Under 249g drone with 4K HDR video and obstacle sensing.",
        "price": 759.99,
        "count_in_stock": 7,
        "rating": 4.7,
        "num_reviews": 8
    },
    {
        "name": "Sonos Era 300 Speaker",
        "image": "/images/sample.jpg",
        "brand": "Sonos",
        "category": "Electronics",
        "description": "Spatial audio speaker with Dolby Atmos support.",
        "price": 449.99,
        "count_in_stock": 11,
        "rating": 4.6,
        "num_reviews": 7
    },
    {
        "name": "LG C3 65-inch OLED TV",
        "image": "/images/screens.png",
        "brand": "LG",
        "category": "Electronics",
        "description": "4K OLED evo with Dolby Vision, 120Hz refresh rate.",
        "detailed_description": "Elevate your entertainment with the LG C3 65-inch OLED evo TV. Self-lit OLED pixels deliver perfect blacks and infinite contrast for stunning picture quality. Brightness Booster enhances brightness up to 70% for vivid HDR. α9 AI Processor Gen6 with AI Picture Pro and AI Sound Pro automatically adjusts picture and sound settings for optimal viewing. 4K resolution at 120Hz with NVIDIA G-SYNC, AMD FreeSync Premium, and VRR support makes this the ultimate gaming TV. Four HDMI 2.1 ports for next-gen gaming consoles. webOS 23 smart platform with built-in streaming apps, Magic Remote included. Dolby Vision IQ and Dolby Atmos for cinematic experience. Filmmaker Mode preserves director's original vision. ThinQ AI and voice control with Alexa, Google Assistant, and Apple AirPlay 2. Gallery Design is slim and elegant to complement any room.",
        "specifications": {
            "Screen Size": "65 inches",
            "Resolution": "4K Ultra HD (3840 x 2160)",
            "Display Type": "OLED evo",
            "Refresh Rate": "120Hz native",
            "HDR": "Dolby Vision IQ, HDR10, HLG",
            "Processor": "α9 AI Processor Gen6",
            "Smart Platform": "webOS 23",
            "HDMI": "4x HDMI 2.1 (4K@120Hz, eARC, VRR, ALLM)",
            "Gaming Features": "NVIDIA G-SYNC, AMD FreeSync Premium, VRR, Game Optimizer",
            "Audio": "40W 2.2ch, Dolby Atmos, AI Sound Pro",
            "Voice Control": "Alexa, Google Assistant, LG ThinQ AI",
            "Connectivity": "Wi-Fi 5, Bluetooth 5.0, Ethernet",
            "Dimensions (with stand)": "57.0\" x 35.4\" x 10.4\"",
            "Weight (with stand)": "55.6 lbs",
            "Remote": "Magic Remote included"
        },
        "price": 1799.99,
        "count_in_stock": 4,
        "rating": 4.9,
        "num_reviews": 16
    },
    {
        "name": "Herman Miller Aeron Chair",
        "image": "/images/sample.jpg",
        "brand": "Herman Miller",
        "category": "Furniture",
        "description": "Ergonomic office chair with PostureFit SL support.",
        "price": 1395.00,
        "count_in_stock": 5,
        "rating": 4.8,
        "num_reviews": 22
    },
    {
        "name": "Secretlab Titan Evo 2022",
        "image": "/images/sample.jpg",
        "brand": "Secretlab",
        "category": "Furniture",
        "description": "Premium gaming chair with 4-way lumbar support.",
        "price": 519.00,
        "count_in_stock": 9,
        "rating": 4.7,
        "num_reviews": 31
    }
]


async def init_db_connection():
    """Initialize database connection"""
    client = AsyncIOMotorClient(settings.MONGO_URI)
    await init_beanie(
        database=client.get_default_database(),
        document_models=[User, Product, Review, Order]
    )


async def generate_reviews(num_reviews: int, avg_rating: float, users: list) -> list:
    """Generate review documents for a product"""
    reviews = []
    
    # Generate ratings that roughly average to the target rating
    for i in range(num_reviews):
        # Bias towards the average rating
        if avg_rating >= 4.5:
            rating = random.choices([5, 4, 3], weights=[70, 25, 5])[0]
        elif avg_rating >= 4.0:
            rating = random.choices([5, 4, 3, 2], weights=[40, 45, 10, 5])[0]
        elif avg_rating >= 3.5:
            rating = random.choices([5, 4, 3, 2], weights=[25, 35, 30, 10])[0]
        else:
            rating = random.choices([5, 4, 3, 2, 1], weights=[15, 25, 30, 20, 10])[0]
        
        # Get a random comment for this rating
        comments = REVIEW_COMMENTS.get(rating, REVIEW_COMMENTS[3])
        comment = random.choice(comments)
        
        # Random date in the past year
        days_ago = random.randint(1, 365)
        created_at = datetime.utcnow() - timedelta(days=days_ago)
        
        # Random reviewer name
        reviewer_name = random.choice(REVIEWER_NAMES)
        
        # Random user from the created users
        user = random.choice(users)
        
        review = Review(
            name=reviewer_name,
            rating=rating,
            comment=comment,
            user=user.id,
            created_at=created_at,
            updated_at=created_at
        )
        await review.insert()
        reviews.append(review)
    
    return reviews


async def import_data():
    """Import sample data"""
    try:
        # Delete existing data
        await Order.delete_all()
        await Review.delete_all()
        await Product.delete_all()
        await User.delete_all()
        
        print("Deleted existing data")
        
        # Insert users
        created_users = []
        for user_data in USERS:
            user = User(**user_data)
            # Password is already hashed, mark it as such
            user.password = user_data["password"]
            await user.insert()
            created_users.append(user)
        
        admin_user = created_users[0]
        print(f"Created {len(created_users)} users")
        
        # Insert products with reviews
        total_reviews = 0
        for raw_product_data in PRODUCTS:
            # Copy so we don't mutate the global PRODUCTS list (we pop fields below)
            product_data = normalize_seed_product(dict(raw_product_data))
            # Pop the fields we'll handle manually
            num_reviews = product_data.pop("num_reviews", 0)
            avg_rating = product_data.pop("rating", 4.0)
            
            # Create the product first without reviews
            product = Product(
                **product_data,
                user=admin_user.id,
                reviews=[],
                num_reviews=0,
                rating=0
            )
            await product.insert()
            
            # Generate and link reviews
            if num_reviews > 0:
                reviews = await generate_reviews(num_reviews, avg_rating, created_users)
                product.reviews = reviews
                
                # Calculate actual rating from reviews
                actual_rating = sum(r.rating for r in reviews) / len(reviews)
                product.rating = round(actual_rating, 1)
                product.num_reviews = len(reviews)
                
                await product.save()
                total_reviews += len(reviews)
        
        print(f"Created {len(PRODUCTS)} products")
        print(f"Created {total_reviews} reviews")
        print("✅ Data Imported Successfully!")
        
    except Exception as error:
        print(f"❌ Error: {error}")
        sys.exit(1)


async def destroy_data():
    """Destroy all data"""
    try:
        await Order.delete_all()
        await Product.delete_all()
        await User.delete_all()
        
        print("✅ Data Destroyed Successfully!")
        
    except Exception as error:
        print(f"❌ Error: {error}")
        sys.exit(1)


async def main():
    """Main function"""
    await init_db_connection()
    
    if len(sys.argv) > 1 and sys.argv[1] == '-d':
        await destroy_data()
    else:
        await import_data()


if __name__ == "__main__":
    asyncio.run(main())
