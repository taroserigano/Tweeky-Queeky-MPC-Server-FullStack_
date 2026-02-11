"""Delete and rebuild Pinecone index"""
import asyncio
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

async def rebuild_pinecone():
    """Delete all vectors from Pinecone and rebuild"""
    
    api_key = os.getenv("PINECONE_API_KEY", "")
    if not api_key or api_key in ("your_key", ""):
        print("ERROR: No Pinecone API key configured")
        return
    
    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=api_key)
        
        index_name = os.getenv("PINECONE_INDEX", "products")
        namespace = os.getenv("PINECONE_NAMESPACE", "products")
        
        print(f"Connecting to Pinecone index: {index_name}")
        index = pc.Index(index_name)
        
        # Delete all vectors in namespace
        print(f"Deleting all vectors in namespace '{namespace}'...")
        index.delete(delete_all=True, namespace=namespace)
        print("✓ Pinecone namespace cleared!")
        
        # Now rebuild using hybrid_search
        from services.hybrid_search import hybrid_engine
        print("\nRebuilding search index...")
        status = await hybrid_engine.initialize()
        print(f"✓ Search index rebuilt: {status}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(rebuild_pinecone())
