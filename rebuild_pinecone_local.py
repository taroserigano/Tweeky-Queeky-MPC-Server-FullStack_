"""Rebuild Pinecone index with correct embeddings"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def rebuild_pinecone():
    """Delete all vectors and rebuild with correct dimensions"""
    
    # Connect to Pinecone
    from pinecone import Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    
    index_name = os.getenv("PINECONE_INDEX", "tweeky-products")
    namespace = os.getenv("PINECONE_NAMESPACE", "products")
    
    print(f"Connecting to Pinecone index: {index_name}")
    index = pc.Index(index_name)
    
    # Delete all vectors
    print(f"Deleting all vectors in namespace '{namespace}'...")
    index.delete(delete_all=True, namespace=namespace)
    print("✓ All vectors deleted!")
    
    # Now fetch products from MongoDB and reindex
    from motor.motor_asyncio import AsyncIOMotorClient
    from openai import AsyncOpenAI
    
    mongo_uri = os.getenv("MONGO_URI")
    client = AsyncIOMotorClient(mongo_uri)
    db = client.get_database("jobify2")
    products_collection = db.get_collection("products")
    
    # Fetch all products
    print("\nFetching products from MongoDB...")
    products = await products_collection.find().to_list(length=None)
    print(f"Found {len(products)} products")
    
    # Initialize OpenAI for embeddings
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    embedding_model = "text-embedding-3-small"  # 1536 dimensions
    
    print(f"\nGenerating embeddings using {embedding_model}...")
    vectors_to_upsert = []
    
    for product in products:
        # Create text for embedding
        text = f"{product.get('name', '')} {product.get('description', '')} {product.get('category', '')} {product.get('brand', '')}"
        
        # Generate embedding
        response = await openai_client.embeddings.create(
            model=embedding_model,
            input=text
        )
        embedding = response.data[0].embedding
        
        vectors_to_upsert.append({
            "id": str(product["_id"]),
            "values": embedding,
            "metadata": {
                "name": product.get("name", ""),
                "description": product.get("description", ""),
                "category": product.get("category", ""),
                "brand": product.get("brand", ""),
                "price": product.get("price", 0),
                "sku": product.get("sku", "")
            }
        })
        
        print(f"  ✓ {product.get('name', 'Unknown')}")
    
    # Upsert to Pinecone in batches
    print(f"\nUpserting {len(vectors_to_upsert)} vectors to Pinecone...")
    batch_size = 100
    for i in range(0, len(vectors_to_upsert), batch_size):
        batch = vectors_to_upsert[i:i+batch_size]
        index.upsert(vectors=batch, namespace=namespace)
        print(f"  Upserted batch {i//batch_size + 1}")
    
    print("\n✅ Pinecone index rebuilt successfully!")
    print(f"   Total vectors: {len(vectors_to_upsert)}")
    print(f"   Embedding model: {embedding_model}")
    print(f"   Dimension: 1536")
    
    # Close connections
    client.close()

if __name__ == "__main__":
    asyncio.run(rebuild_pinecone())
