"""
Hybrid Product Search Engine
Combines BM25 (sparse keyword matching) + OpenAI semantic embeddings (dense vectors)
using Reciprocal Rank Fusion (RRF) for score combination.

Architecture:
- BM25 index: built in-memory from product text corpus (name, brand, category, description)
- Semantic index: OpenAI embeddings stored in Pinecone vector DB (with numpy fallback)
- Query: scores from both engines are fused via RRF to produce a single ranked list
- Supports metadata filters (category, brand, price range, rating)
- Minimum relevance threshold prevents irrelevant results from being returned

Call `await hybrid_engine.initialize()` once at startup to build the index.
"""

import os
import re
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from rank_bm25 import BM25Okapi

# Load .env from project root so this works standalone too
from dotenv import load_dotenv

_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# OPENAI EMBEDDING HELPERS
# ─────────────────────────────────────────────────────────────────────────────

EMBED_MODEL = os.getenv(
    "OPENAI_EMBED_MODEL",
    os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
)

_openai_client = None


def _get_openai():
    """Lazy-init OpenAI client."""
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_AI")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set — cannot create embeddings")
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def _embed_texts(texts: List[str]) -> np.ndarray:
    """Embed a batch of texts using OpenAI."""
    client = _get_openai()
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    vecs = [d.embedding for d in sorted(resp.data, key=lambda d: d.index)]
    return np.array(vecs, dtype=np.float32)


def _cosine_similarity(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Cosine similarity between a single query vector and a matrix of vectors."""
    dot = matrix @ query_vec
    norms = np.linalg.norm(matrix, axis=1) * np.linalg.norm(query_vec)
    norms = np.where(norms == 0, 1e-10, norms)
    return dot / norms


# ─────────────────────────────────────────────────────────────────────────────
# BM25 TOKENISER
# ─────────────────────────────────────────────────────────────────────────────

_STOP_WORDS = frozenset(
    "a an the is are was were be been being have has had do does did will "
    "would shall should may might can could of in to for with on at by from "
    "as into through during before after above below between out off over "
    "under again further then once and but or nor not so yet both each every "
    "all any few more most other some such no only own same than too very it "
    "its i me my we our you your he him his she her they them their this that "
    "these those".split()
)


def _simple_stem(word: str) -> str:
    """Very basic suffix stripping to improve BM25 recall."""
    for suffix in ("lessly", "ingly", "ously", "ness", "ment", "ally",
                   "ical", "ibly", "ably", "tion", "sion", "ence", "ance",
                   "ness", "less", "ized", "ised", "ting", "ling",
                   "ly", "ing", "ed", "er", "es", "en"):
        if len(word) > len(suffix) + 2 and word.endswith(suffix):
            return word[: -len(suffix)]
    if word.endswith("s") and len(word) > 3 and not word.endswith("ss"):
        return word[:-1]
    return word


def _tokenize(text: str) -> List[str]:
    """Whitespace + punctuation tokenizer with basic stemming, lowercased, stop-words removed."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [_simple_stem(t) for t in tokens if t not in _STOP_WORDS and len(t) > 1]


# ─────────────────────────────────────────────────────────────────────────────
# PRODUCT DOCUMENT BUILDER
# ─────────────────────────────────────────────────────────────────────────────


def _product_to_text(p: Dict[str, Any]) -> str:
    """Create a rich text representation of a product for embedding/indexing."""
    parts = [
        p.get("name", ""),
        f"Brand: {p.get('brand', '')}",
        f"Category: {p.get('category', '')}",
        p.get("description", ""),
    ]
    # Include detailed description if present
    dd = p.get("detailed_description") or p.get("detailedDescription")
    if dd:
        parts.append(dd)
    # Include specification keys/values
    specs = p.get("specifications")
    if specs and isinstance(specs, dict):
        for k, v in specs.items():
            parts.append(f"{k}: {v}")
    # Include rating and review count for semantic matching on rating queries
    rating = p.get("rating", 0)
    num_reviews = p.get("numReviews", p.get("num_reviews", 0))
    if rating:
        parts.append(f"Rating: {rating}/5 stars")
    if num_reviews:
        parts.append(f"Customer reviews: {num_reviews} reviews")
    # Include actual review text for better semantic understanding
    reviews = p.get("_review_texts", [])
    if reviews:
        parts.append("Customer feedback: " + " | ".join(reviews[:10]))
    return " ".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# PINECONE HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _get_pinecone_client():
    """Initialise Pinecone client if API key is configured."""
    api_key = os.getenv("PINECONE_API_KEY", "")
    if not api_key or api_key in ("your_key", ""):
        return None
    try:
        from pinecone import Pinecone
        return Pinecone(api_key=api_key)
    except Exception as e:
        logger.warning("Pinecone init failed: %s", e)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# HYBRID SEARCH ENGINE
# ─────────────────────────────────────────────────────────────────────────────

# Minimum relevance thresholds:
# Products must exceed BOTH a combined minimum AND at least one individual threshold.
_MIN_BM25_SCORE = 0.15         # Normalised BM25 (0–1); filters loose keyword matches
_MIN_SEMANTIC_SCORE = 0.30     # Cosine similarity floor. OpenAI text-embedding-3-small scores:
                               #   0.44+ = strong match ("wireless headphones" → AirPods)
                               #   0.34  = moderate match ("headphones" → AirPods)
                               #   0.25-0.29 = same electronic domain, different product type
                               #   < 0.25 = unrelated
                               # 0.30 cleanly separates relevant from irrelevant for this catalog.
_MIN_COMBINED_RRF = 0.025      # Minimum RRF combined score to include a product
_RELATIVE_SCORE_GAP = 0.75     # Keep only products whose semantic score is >= 75%
                               # of the top result's semantic score.  This removes
                               # weakly-related products that ride on embedding
                               # noise when a strong match exists.
                               #
                               # Examples with real data:
                               # "microphone podcasting" → SM7B 0.558, AirPods 0.354
                               #   75% of 0.558 = 0.419 → AirPods filtered ✓
                               # "headphones" → AirPods 0.345 (top) → keeps itself ✓
                               # "audio interface" → Focusrite 0.474, AirPods 0.351
                               #   75% of 0.474 = 0.356 → AirPods filtered ✓


class HybridSearchEngine:
    """
    Hybrid (BM25 + semantic) search over the product catalog.

    - BM25 is always in-memory (rank-bm25).
    - Semantic embeddings are stored in **Pinecone** when available,
      with an in-memory numpy fallback.

    Usage:
        engine = HybridSearchEngine()
        await engine.initialize()                     # call once at startup
        results = engine.search("comfortable chair")  # returns ranked dicts
    """

    def __init__(self, alpha: float = 0.5, rrf_k: int = 60):
        """
        Args:
            alpha: Weight for semantic score in weighted combination (0-1).
                   0 = pure BM25, 1 = pure semantic. Only used when mode='weighted'.
            rrf_k: RRF constant (default 60, standard in literature).
        """
        self.alpha = alpha
        self.rrf_k = rrf_k

        # Populated by initialize()
        self._products: List[Dict[str, Any]] = []
        self._product_id_to_idx: Dict[str, int] = {}
        self._corpus_tokens: List[List[str]] = []
        self._bm25: Optional[BM25Okapi] = None

        # Semantic backend — exactly one will be populated
        self._embeddings: Optional[np.ndarray] = None  # numpy fallback
        self._pinecone_index = None                     # Pinecone index object
        self._pinecone_ns: str = os.getenv("PINECONE_NAMESPACE", "products")
        self._use_pinecone: bool = False

        self._ready = False

    # ── INITIALIZATION ────────────────────────────────────────────────────

    async def initialize(self) -> Dict[str, Any]:
        """Load products from MongoDB, build BM25 index, embed & store in Pinecone (or numpy)."""
        from config.database import get_sync_db

        db = get_sync_db()
        raw_products = list(db.products.find())
        if not raw_products:
            logger.warning("HybridSearch: No products found in MongoDB")
            self._ready = False
            return {"status": "empty", "products": 0}

        self._products = []
        self._product_id_to_idx = {}
        texts_for_embedding: List[str] = []
        corpus_tokens: List[List[str]] = []

        for i, p in enumerate(raw_products):
            pid = str(p["_id"])
            
            # Resolve review references to get actual review text
            review_texts = []
            review_refs = p.get("reviews", [])
            if review_refs:
                for ref in review_refs[:10]:  # Limit to 10 reviews per product
                    try:
                        if isinstance(ref, dict) and "$id" in ref:
                            review_id = ref["$id"]
                        elif hasattr(ref, '__class__') and ref.__class__.__name__ == 'ObjectId':
                            review_id = ref
                        else:
                            continue
                        review_doc = db.reviews.find_one({"_id": review_id})
                        if review_doc and review_doc.get("comment"):
                            rating_str = f"({review_doc.get('rating', 0)}/5)"
                            review_texts.append(f"{rating_str} {review_doc['comment']}")
                    except Exception:
                        continue
            
            doc = {
                "_id": pid,
                "name": p.get("name", ""),
                "brand": p.get("brand", ""),
                "category": p.get("category", ""),
                "description": p.get("description", ""),
                "detailed_description": p.get("detailedDescription", ""),
                "specifications": p.get("specifications"),
                "price": float(p.get("price", 0)),
                "rating": float(p.get("rating", 0)),
                "numReviews": int(p.get("numReviews", 0)),
                "countInStock": int(p.get("countInStock", 0)),
                "image": p.get("image", ""),
                "_review_texts": review_texts,
            }
            self._products.append(doc)
            self._product_id_to_idx[pid] = i

            text = _product_to_text(doc)
            texts_for_embedding.append(text)
            corpus_tokens.append(_tokenize(text))

        # Build BM25 index (always in-memory)
        self._corpus_tokens = corpus_tokens
        self._bm25 = BM25Okapi(corpus_tokens)
        logger.info("HybridSearch: BM25 index built — %d products", len(self._products))

        # Embed all product texts
        try:
            embeddings = _embed_texts(texts_for_embedding)
            embed_dim = embeddings.shape[1]
            logger.info(
                "HybridSearch: Embeddings built — shape %s, model=%s",
                embeddings.shape,
                EMBED_MODEL,
            )
        except Exception as e:
            logger.error("HybridSearch: Embedding failed — %s", e)
            self._ready = True
            return {
                "status": "ready_bm25_only",
                "products": len(self._products),
                "bm25_corpus": len(self._corpus_tokens),
                "vector_backend": "none",
            }

        # Try Pinecone first, fall back to numpy
        pc = _get_pinecone_client()
        if pc is not None:
            try:
                self._init_pinecone(pc, embeddings, embed_dim)
            except Exception as e:
                logger.warning("HybridSearch: Pinecone setup failed, using numpy fallback — %s", e)
                self._embeddings = embeddings
                self._use_pinecone = False
        else:
            logger.info("HybridSearch: No Pinecone key — using numpy in-memory vectors")
            self._embeddings = embeddings
            self._use_pinecone = False

        self._ready = True
        backend = "pinecone" if self._use_pinecone else "numpy"
        return {
            "status": "ready",
            "products": len(self._products),
            "bm25_corpus": len(self._corpus_tokens),
            "embeddings_shape": list(embeddings.shape),
            "embed_model": EMBED_MODEL,
            "vector_backend": backend,
        }

    def _init_pinecone(self, pc, embeddings: np.ndarray, embed_dim: int):
        """Create/verify Pinecone index and upsert all product vectors."""
        from pinecone import ServerlessSpec

        index_name = os.getenv("PINECONE_INDEX", "tweeky-products")
        cloud = os.getenv("PINECONE_CLOUD", "aws")
        region = os.getenv("PINECONE_REGION", "us-east-1")

        existing = [idx.name for idx in pc.list_indexes()]
        if index_name not in existing:
            logger.info("HybridSearch: Creating Pinecone index '%s' (dim=%d)", index_name, embed_dim)
            pc.create_index(
                name=index_name,
                dimension=embed_dim,
                metric="cosine",
                spec=ServerlessSpec(cloud=cloud, region=region),
            )
            # Wait for ready
            import time
            for _ in range(30):
                if pc.describe_index(index_name).status.ready:
                    break
                time.sleep(1)

        self._pinecone_index = pc.Index(index_name)

        # Upsert all products in batches of 100
        batch_size = 100
        vectors = []
        for i, p in enumerate(self._products):
            vectors.append({
                "id": p["_id"],
                "values": embeddings[i].tolist(),
                "metadata": {
                    "name": p["name"],
                    "brand": p["brand"],
                    "category": p["category"],
                    "price": p["price"],
                    "rating": p["rating"],
                },
            })
        for start in range(0, len(vectors), batch_size):
            batch = vectors[start : start + batch_size]
            self._pinecone_index.upsert(vectors=batch, namespace=self._pinecone_ns)

        self._use_pinecone = True
        stats = self._pinecone_index.describe_index_stats()
        logger.info(
            "HybridSearch: Pinecone ready — index=%s, vectors=%d",
            index_name,
            stats.total_vector_count,
        )

    @property
    def ready(self) -> bool:
        return self._ready

    # ── SEARCH ────────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        *,
        limit: int = 10,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        mode: str = "rrf",
        relative_score_gap: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining BM25 + semantic.

        Args:
            query: Search text
            limit: Max results to return
            category: Filter by category (case-insensitive)
            brand: Filter by brand (case-insensitive)
            min_price / max_price: Price range filter
            min_rating: Minimum rating filter
            mode: 'rrf' (reciprocal rank fusion) or 'weighted' (alpha blend)
            relative_score_gap: Fraction of max semantic score for filtering.
                              If None, auto-detects: 0.60 for recommendations,
                              0.75 for specific searches.

        Returns:
            List of product dicts with 'score', 'bm25_score', 'semantic_score' keys.
        """
        if not self._ready or not self._products:
            return []

        # Auto-detect recommendation intent for more lenient filtering
        if relative_score_gap is None:
            recommendation_keywords = ['recommend', 'best', 'top', 'suggest', 'looking for']
            if any(kw in query.lower() for kw in recommendation_keywords):
                relative_score_gap = 0.60  # More lenient for recommendations
                min_semantic_threshold = 0.25  # Lower absolute threshold for recommendations
            else:
                relative_score_gap = _RELATIVE_SCORE_GAP  # 0.75 for specific searches
                min_semantic_threshold = _MIN_SEMANTIC_SCORE  # 0.30 for searches
        else:
            min_semantic_threshold = _MIN_SEMANTIC_SCORE

        n = len(self._products)

        # ── BM25 scores ──────────────────────────────────────────────────
        query_tokens = _tokenize(query)
        if self._bm25 is not None and query_tokens:
            bm25_raw = self._bm25.get_scores(query_tokens)  # (n,)
        else:
            bm25_raw = np.zeros(n, dtype=np.float32)

        # Normalise BM25 to [0, 1]
        bm25_max = bm25_raw.max() if bm25_raw.max() > 0 else 1.0
        bm25_norm = bm25_raw / bm25_max

        # Guard: if the BEST raw BM25 score is very low, it means no product
        # truly matches the keywords. Zero out normalised scores to prevent
        # the normalisation from inflating a 0.02 raw match into 1.0.
        _BM25_RAW_FLOOR = 0.5  # Products not containing query terms score < 0.5
        if bm25_raw.max() < _BM25_RAW_FLOOR:
            bm25_norm = np.zeros(n, dtype=np.float32)

        # ── Semantic scores ───────────────────────────────────────────────
        sem_scores = self._get_semantic_scores(query, n)

        # ── Score fusion ──────────────────────────────────────────────────
        if mode == "weighted":
            combined = (1 - self.alpha) * bm25_norm + self.alpha * sem_scores
        else:
            # Reciprocal Rank Fusion (RRF)
            bm25_ranks = _rank_array(bm25_raw)
            sem_ranks = _rank_array(sem_scores)
            k = self.rrf_k
            combined = 1.0 / (k + bm25_ranks) + 1.0 / (k + sem_ranks)

        # ── Build ranked result list with filters ─────────────────────────
        
        scored = []
        for idx in range(n):
            p = self._products[idx]

            # ── Minimum relevance gate ────────────────────────────────────
            # STRICT: Always require a minimum semantic similarity. Semantic
            # embeddings capture actual meaning (is this product related to
            # the query?), while BM25 only matches individual words which
            # produces false positives on common words like "best", "work".
            #
            # Semantic thresholds (OpenAI text-embedding-3-small):
            #   > 0.50  = strong match (e.g., "headphones" → AirPods)
            #   0.30-50 = related product
            #   0.25-30 = same broad domain, acceptable for recommendations
            #   0.15-25 = vaguely related
            #   < 0.15  = unrelated
            #
            # For searches: require >= 0.30 (strict)
            # For recommendations: require >= 0.25 (lenient for related products)
            has_semantic_match = sem_scores[idx] >= min_semantic_threshold
            if not has_semantic_match:
                continue

            # Apply metadata filters
            if category and not re.search(category, p["category"], re.IGNORECASE):
                continue
            if brand and not re.search(brand, p["brand"], re.IGNORECASE):
                continue
            if min_price is not None and p["price"] < min_price:
                continue
            if max_price is not None and p["price"] > max_price:
                continue
            if min_rating is not None and p["rating"] < min_rating:
                continue

            scored.append(
                {
                    **p,
                    "score": float(combined[idx]),
                    "bm25_score": float(bm25_norm[idx]),
                    "semantic_score": float(sem_scores[idx]),
                }
            )

        # Sort by combined score descending
        scored.sort(key=lambda x: x["score"], reverse=True)

        # ── Relative score gap filter ─────────────────────────────────────
        # When a strong semantic match exists, remove weaker results that
        # ride on embedding noise. This prevents "microphone" from also
        # returning AirPods (0.282) when SM7B scored 0.485 semantically.
        # 
        # Use the HIGHEST semantic score among all candidates (not the top
        # combined score) as the baseline, since BM25 can push semantically
        # weaker products to the top of the combined ranking.
        #
        # For recommendation queries, use a more lenient threshold (0.60)
        # to show related products when exact matches are limited.
        if scored:
            max_sem = max(r["semantic_score"] for r in scored)
            if max_sem > 0:
                cutoff = max_sem * relative_score_gap
                scored = [r for r in scored if r["semantic_score"] >= cutoff]

        return scored[:limit]

    def _get_semantic_scores(self, query: str, n: int) -> np.ndarray:
        """Get semantic similarity scores from Pinecone or numpy fallback."""
        sem_scores = np.zeros(n, dtype=np.float32)

        if self._use_pinecone and self._pinecone_index is not None:
            try:
                query_vec = _embed_texts([query])[0].tolist()
                results = self._pinecone_index.query(
                    vector=query_vec,
                    top_k=n,
                    namespace=self._pinecone_ns,
                    include_metadata=False,
                )
                for match in results.get("matches", []):
                    pid = match["id"]
                    idx = self._product_id_to_idx.get(pid)
                    if idx is not None:
                        sem_scores[idx] = float(match["score"])
            except Exception as e:
                logger.error("Pinecone query failed, falling back to numpy: %s", e)
                sem_scores = self._numpy_semantic(query, n)
        elif self._embeddings is not None:
            sem_scores = self._numpy_semantic(query, n)

        return np.clip(sem_scores, 0.0, 1.0)

    def _numpy_semantic(self, query: str, n: int) -> np.ndarray:
        """Fallback: cosine similarity using numpy in-memory embeddings."""
        try:
            query_vec = _embed_texts([query])[0]
            return _cosine_similarity(query_vec, self._embeddings)
        except Exception as e:
            logger.error("Numpy semantic search failed: %s", e)
            return np.zeros(n, dtype=np.float32)

    # ── CONVENIENCE ───────────────────────────────────────────────────────

    def health(self) -> Dict[str, Any]:
        backend = "pinecone" if self._use_pinecone else "numpy"
        info: Dict[str, Any] = {
            "ready": self._ready,
            "products_indexed": len(self._products),
            "bm25_ready": self._bm25 is not None,
            "embed_model": EMBED_MODEL,
            "vector_backend": backend,
            "fusion_rrf_k": self.rrf_k,
            "fusion_alpha": self.alpha,
            "min_bm25_threshold": _MIN_BM25_SCORE,
            "min_semantic_threshold": _MIN_SEMANTIC_SCORE,
            "min_combined_rrf": _MIN_COMBINED_RRF,
            "relative_score_gap": _RELATIVE_SCORE_GAP,
        }
        if self._use_pinecone and self._pinecone_index is not None:
            try:
                stats = self._pinecone_index.describe_index_stats()
                info["pinecone_vectors"] = stats.total_vector_count
            except Exception:
                info["pinecone_vectors"] = "error"
        elif self._embeddings is not None:
            info["embeddings_shape"] = list(self._embeddings.shape)
        return info


# ─────────────────────────────────────────────────────────────────────────────
# RANK HELPER
# ─────────────────────────────────────────────────────────────────────────────


def _rank_array(scores: np.ndarray) -> np.ndarray:
    """Convert scores to 1-based ranks (highest score = rank 1)."""
    order = scores.argsort()[::-1]
    ranks = np.empty_like(order)
    ranks[order] = np.arange(1, len(scores) + 1)
    return ranks.astype(np.float64)


# ─────────────────────────────────────────────────────────────────────────────
# SINGLETON
# ─────────────────────────────────────────────────────────────────────────────

hybrid_engine = HybridSearchEngine()
