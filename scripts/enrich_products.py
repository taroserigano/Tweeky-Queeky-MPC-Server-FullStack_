"""Backfill richer product data.

- Adds `detailedDescription` when missing
- Normalizes placeholder images to `/images/sample.png`

This script does NOT delete any data.
"""

from __future__ import annotations

import sys
from pathlib import Path

from pymongo import MongoClient

# Allow running as a script from any working directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings


def build_detailed_description(name: str, brand: str, category: str, short_description: str) -> str:
    clean_name = (name or "").strip() or "This item"
    clean_brand = (brand or "").strip()
    clean_category = (category or "").strip()
    clean_short = (short_description or "").strip()

    parts: list[str] = []
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
        "If you want, ask for a comparison with similar options and I’ll highlight key differences."
    )

    return " ".join(p.strip().rstrip(".") + "." for p in parts if p and p.strip())


def main() -> None:
    try:
        client = MongoClient(
            settings.MONGO_URI,
            serverSelectionTimeoutMS=8000,
            connectTimeoutMS=8000,
            socketTimeoutMS=8000,
        )
        # Force an early connection attempt so DNS/SRV issues fail fast
        client.admin.command("ping")
    except Exception as e:
        raise SystemExit(
            "Failed to connect to MongoDB. If you're using a `mongodb+srv://...` URI, "
            "this often means SRV/TXT DNS lookups are blocked on your network. "
            "Try switching `MONGO_URI` to a non-SRV `mongodb://host1,host2,...` connection string, "
            "or run this script on a network that allows DNS SRV queries.\n\n"
            f"Original error: {e}"
        )
    db = client.get_default_database()
    products = db.products

    updated = 0
    backfilled = 0
    normalized_images = 0
    backfilled_sku = 0

    cursor = products.find(
        {},
        {
            "name": 1,
            "brand": 1,
            "category": 1,
            "description": 1,
            "detailedDescription": 1,
            "image": 1,
            "sku": 1,
        },
    )
    for doc in cursor:
        set_ops: dict = {}

        if not doc.get("sku"):
            set_ops["sku"] = f"SKU-{str(doc['_id']).upper()}"
            backfilled_sku += 1

        if not doc.get("detailedDescription"):
            set_ops["detailedDescription"] = build_detailed_description(
                doc.get("name", ""),
                doc.get("brand", ""),
                doc.get("category", ""),
                doc.get("description", ""),
            )
            backfilled += 1

        image = doc.get("image")
        if not image or image in {"/images/sample.jpg", "/images/sample.jpeg"}:
            set_ops["image"] = "/images/sample.png"
            normalized_images += 1

        if set_ops:
            products.update_one({"_id": doc["_id"]}, {"$set": set_ops})
            updated += 1

    print("✅ Product enrichment complete")
    print(f"Updated documents: {updated}")
    print(f"Backfilled detailedDescription: {backfilled}")
    print(f"Normalized placeholder images: {normalized_images}")
    print(f"Backfilled sku: {backfilled_sku}")


if __name__ == "__main__":
    main()
