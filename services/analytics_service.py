"""
Analytics Service - Sentiment analysis, trends, and insights

Handles review sentiment analysis, sales trends, and customer behavior insights.
Used by both REST API endpoints and MCP tools.
"""

from typing import Optional, List, Dict, Any
from collections import Counter
from bson import ObjectId

from models.product import Product, Review
from models.order import Order


class AnalyticsService:
    """Service class for analytics and insights"""
    
    # Sentiment word lists (can be extended or replaced with ML model)
    POSITIVE_WORDS = {
        "great", "love", "excellent", "amazing", "good", "best", "perfect",
        "awesome", "fantastic", "happy", "wonderful", "superb", "outstanding",
        "brilliant", "incredible", "recommend", "satisfied", "pleased",
        "quality", "worth", "reliable", "sturdy", "comfortable", "fast"
    }
    
    NEGATIVE_WORDS = {
        "bad", "poor", "terrible", "worst", "hate", "broken", "waste",
        "disappointed", "awful", "useless", "defective", "cheap", "flimsy",
        "slow", "horrible", "frustrating", "regret", "return", "refund",
        "faulty", "damaged", "overpriced", "uncomfortable", "unreliable"
    }
    
    NEUTRAL_MODIFIERS = {"not", "no", "never", "none", "neither", "nor", "barely"}

    # ──────────────────────────────────────────────────────────────────────────
    # SENTIMENT ANALYSIS
    # ──────────────────────────────────────────────────────────────────────────

    def _analyze_text_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of a single text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment data with score and label
        """
        words = text.lower().split()
        word_set = set(words)
        
        # Check for negation modifiers
        has_negation = bool(word_set & self.NEUTRAL_MODIFIERS)
        
        pos_count = len(word_set & self.POSITIVE_WORDS)
        neg_count = len(word_set & self.NEGATIVE_WORDS)
        
        # Simple negation handling: if negation present, flip sentiment
        if has_negation:
            pos_count, neg_count = neg_count, pos_count
        
        # Calculate score (-1 to 1)
        total = pos_count + neg_count
        if total == 0:
            score = 0.0
            label = "neutral"
        else:
            score = (pos_count - neg_count) / total
            if score > 0.2:
                label = "positive"
            elif score < -0.2:
                label = "negative"
            else:
                label = "neutral"
        
        return {
            "score": round(score, 2),
            "label": label,
            "positive_words": pos_count,
            "negative_words": neg_count,
        }

    async def get_reviews_sentiment(
        self,
        product_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze sentiment of reviews for a product or all reviews.
        
        Args:
            product_id: Optional product ID (if None, analyzes all reviews)
            
        Returns:
            Sentiment summary with counts and percentages
        """
        if product_id:
            try:
                oid = ObjectId(product_id)
            except Exception:
                raise ValueError(f"Invalid product ID: {product_id}")
            
            product = await Product.get(oid, fetch_links=True)
            if not product:
                raise ValueError("Product not found")
            reviews = product.reviews or []
        else:
            reviews = await Review.find().to_list()
        
        if not reviews:
            return {
                "total_reviews": 0,
                "positive": 0,
                "neutral": 0,
                "negative": 0,
                "average_sentiment_score": 0.0,
            }
        
        positive, neutral, negative = 0, 0, 0
        total_score = 0.0
        
        for review in reviews:
            sentiment = self._analyze_text_sentiment(review.comment)
            total_score += sentiment["score"]
            
            if sentiment["label"] == "positive":
                positive += 1
            elif sentiment["label"] == "negative":
                negative += 1
            else:
                neutral += 1
        
        total = len(reviews)
        
        return {
            "total_reviews": total,
            "positive": positive,
            "neutral": neutral,
            "negative": negative,
            "positive_pct": round(positive / total * 100, 1),
            "neutral_pct": round(neutral / total * 100, 1),
            "negative_pct": round(negative / total * 100, 1),
            "average_sentiment_score": round(total_score / total, 2),
        }

    async def get_review_keywords(
        self,
        product_id: Optional[str] = None,
        top_n: int = 10,
    ) -> Dict[str, Any]:
        """
        Extract most common keywords from reviews.
        
        Args:
            product_id: Optional product ID
            top_n: Number of top keywords to return
            
        Returns:
            Top positive and negative keywords
        """
        if product_id:
            try:
                oid = ObjectId(product_id)
            except Exception:
                raise ValueError(f"Invalid product ID: {product_id}")
            
            product = await Product.get(oid, fetch_links=True)
            if not product:
                raise ValueError("Product not found")
            reviews = product.reviews or []
        else:
            reviews = await Review.find().to_list()
        
        positive_found: List[str] = []
        negative_found: List[str] = []
        
        for review in reviews:
            words = set(review.comment.lower().split())
            positive_found.extend(words & self.POSITIVE_WORDS)
            negative_found.extend(words & self.NEGATIVE_WORDS)
        
        pos_counter = Counter(positive_found)
        neg_counter = Counter(negative_found)
        
        return {
            "total_reviews": len(reviews),
            "top_positive_keywords": [
                {"word": word, "count": count}
                for word, count in pos_counter.most_common(top_n)
            ],
            "top_negative_keywords": [
                {"word": word, "count": count}
                for word, count in neg_counter.most_common(top_n)
            ],
        }

    # ──────────────────────────────────────────────────────────────────────────
    # PRODUCT PERFORMANCE
    # ──────────────────────────────────────────────────────────────────────────

    async def get_top_performers(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get top performing products by various metrics.
        
        Returns:
            Top products by rating, reviews, and combined score
        """
        products = await Product.find().to_list()
        if not products:
            return {"by_rating": [], "by_reviews": [], "by_combined": []}
        
        def to_dict(p: Product) -> Dict[str, Any]:
            return {
                "id": str(p.id),
                "name": p.name,
                "brand": p.brand,
                "rating": p.rating,
                "num_reviews": p.num_reviews,
                "price": p.price,
            }
        
        # By rating
        by_rating = sorted(products, key=lambda p: p.rating, reverse=True)[:limit]
        
        # By review count
        by_reviews = sorted(products, key=lambda p: p.num_reviews, reverse=True)[:limit]
        
        # Combined score (normalized rating * log(reviews+1))
        import math
        for p in products:
            p._combined_score = p.rating * math.log(p.num_reviews + 1)
        by_combined = sorted(products, key=lambda p: p._combined_score, reverse=True)[:limit]
        
        return {
            "by_rating": [to_dict(p) for p in by_rating],
            "by_reviews": [to_dict(p) for p in by_reviews],
            "by_combined_score": [
                {**to_dict(p), "combined_score": round(p._combined_score, 2)}
                for p in by_combined
            ],
        }

    async def get_category_performance(self) -> List[Dict[str, Any]]:
        """
        Get performance metrics per category.
        
        Returns:
            List of category performance data
        """
        products = await Product.find().to_list()
        
        by_cat: Dict[str, List[Product]] = {}
        for p in products:
            by_cat.setdefault(p.category, []).append(p)
        
        results = []
        for cat, items in by_cat.items():
            ratings = [p.rating for p in items]
            reviews = [p.num_reviews for p in items]
            
            results.append({
                "category": cat,
                "product_count": len(items),
                "avg_rating": round(sum(ratings) / len(ratings), 2),
                "total_reviews": sum(reviews),
                "avg_reviews_per_product": round(sum(reviews) / len(items), 1),
            })
        
        return sorted(results, key=lambda x: x["avg_rating"], reverse=True)

    # ──────────────────────────────────────────────────────────────────────────
    # RATINGS ANALYSIS
    # ──────────────────────────────────────────────────────────────────────────

    async def get_rating_distribution(
        self,
        product_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get distribution of ratings (1-5 stars).
        
        Args:
            product_id: Optional product ID
            
        Returns:
            Rating distribution with counts and percentages
        """
        if product_id:
            try:
                oid = ObjectId(product_id)
            except Exception:
                raise ValueError(f"Invalid product ID: {product_id}")
            
            product = await Product.get(oid, fetch_links=True)
            if not product:
                raise ValueError("Product not found")
            reviews = product.reviews or []
        else:
            reviews = await Review.find().to_list()
        
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        for review in reviews:
            if 1 <= review.rating <= 5:
                distribution[review.rating] += 1
        
        total = len(reviews)
        
        return {
            "total_reviews": total,
            "distribution": [
                {
                    "stars": stars,
                    "count": count,
                    "percentage": round(count / total * 100, 1) if total > 0 else 0,
                }
                for stars, count in sorted(distribution.items(), reverse=True)
            ],
            "average_rating": round(
                sum(r.rating for r in reviews) / total, 2
            ) if total > 0 else 0,
        }


# Singleton instance for easy import
analytics_service = AnalyticsService()
