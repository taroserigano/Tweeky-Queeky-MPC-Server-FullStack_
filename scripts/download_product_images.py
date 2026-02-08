#!/usr/bin/env python3
"""
Download real product images from the web for all products in MongoDB.

Uses DuckDuckGo Image Search (free, no API key needed) to find actual
product photos, downloads them, saves to frontend/public/images/,
and updates the MongoDB `image` field.

Usage:
    pip install duckduckgo-search Pillow
    python scripts/download_product_images.py
"""

import os
import sys
import re
import time
import io

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from pathlib import Path
from PIL import Image

from config.database import get_sync_db

IMAGE_DIR = Path("frontend/public/images")
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# Target image size - consistent product cards
TARGET_WIDTH = 640
TARGET_HEIGHT = 640
JPEG_QUALITY = 85

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
}


def slugify(name: str) -> str:
    """Convert product name to a clean filename slug."""
    slug = re.sub(r'[^\w\s-]', '', name.lower())
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug


def process_image(raw_bytes: bytes, output_path: Path) -> bool:
    """Resize and save image as optimized JPEG."""
    try:
        img = Image.open(io.BytesIO(raw_bytes))
        img = img.convert("RGB")

        # Resize to fit within target dimensions, maintaining aspect ratio
        img.thumbnail((TARGET_WIDTH, TARGET_HEIGHT), Image.LANCZOS)

        # Create white background canvas and center the product image
        canvas = Image.new("RGB", (TARGET_WIDTH, TARGET_HEIGHT), (255, 255, 255))
        x_offset = (TARGET_WIDTH - img.width) // 2
        y_offset = (TARGET_HEIGHT - img.height) // 2
        canvas.paste(img, (x_offset, y_offset))

        canvas.save(output_path, "JPEG", quality=JPEG_QUALITY, optimize=True)
        return True
    except Exception as e:
        print(f"    Image processing error: {e}")
        return False


def search_and_download(product_name: str, brand: str = "") -> str | None:
    """Search DuckDuckGo for a product image and download it."""
    from duckduckgo_search import DDGS

    # Build search query - try different variations
    search_terms = [
        f"{product_name} product",
        f"{brand} {product_name}" if brand else product_name,
    ]

    for qi, query in enumerate(search_terms):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.images(query, max_results=5))

            if not results:
                time.sleep(3)
                continue

            # Try each image result
            for result in results:
                img_url = result.get("image", "")
                if not img_url:
                    continue

                # Skip tiny thumbnails and SVGs
                if any(skip in img_url.lower() for skip in [".svg", "1x1", "pixel", "blank", "spacer"]):
                    continue

                try:
                    resp = requests.get(img_url, timeout=15, headers=HEADERS)
                    if resp.status_code == 200 and len(resp.content) > 5000:
                        # Save as clean JPEG
                        filename = slugify(product_name) + ".jpg"
                        filepath = IMAGE_DIR / filename

                        if process_image(resp.content, filepath):
                            return f"/images/{filename}"
                except requests.RequestException:
                    continue

        except Exception as e:
            print(f"\n    Search error for '{query}': {e}")
            # On rate limit, wait longer
            if "Ratelimit" in str(e) or "403" in str(e):
                print(f"    Rate limited, waiting 30s...")
                time.sleep(30)
            continue

        # Wait between search query attempts
        time.sleep(5)

    return None


def main():
    db = get_sync_db()
    products = list(db.products.find({}))

    print(f"=" * 60)
    print(f"  Product Image Downloader")
    print(f"  Products: {len(products)}")
    print(f"  Output: {IMAGE_DIR.absolute()}")
    print(f"=" * 60)
    print()

    updated = 0
    failed = 0
    skipped = 0

    for i, product in enumerate(products, 1):
        name = product.get("name", "Unknown")
        brand = product.get("brand", "")
        old_image = product.get("image", "")

        # Check if we already have a real JPEG for this product
        expected_jpg = IMAGE_DIR / (slugify(name) + ".jpg")
        if expected_jpg.exists() and expected_jpg.stat().st_size > 5000:
            print(f"[{i:2d}/{len(products)}] {name[:45]:45s} SKIP (already have .jpg)")
            skipped += 1
            # Still update DB to point to the jpg
            new_path = f"/images/{expected_jpg.name}"
            if old_image != new_path:
                db.products.update_one({"_id": product["_id"]}, {"$set": {"image": new_path}})
            continue

        print(f"[{i:2d}/{len(products)}] {name[:45]:45s} ", end="", flush=True)

        new_image = search_and_download(name, brand)

        if new_image:
            # Update MongoDB
            db.products.update_one(
                {"_id": product["_id"]},
                {"$set": {"image": new_image}}
            )
            print(f"OK -> {new_image}")
            updated += 1
        else:
            print(f"FAILED (keeping {old_image})")
            failed += 1

        # Rate limit - be respectful to DuckDuckGo
        time.sleep(8)

    print()
    print(f"=" * 60)
    print(f"  Results: {updated} downloaded, {skipped} skipped, {failed} failed")
    print(f"=" * 60)

    if failed > 0:
        print(f"\n  {failed} products still have old/fake images.")
        print(f"  Re-run this script to retry failed downloads.")


if __name__ == "__main__":
    main()
