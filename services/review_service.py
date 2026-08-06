from typing import Optional, List, Dict, Any
from database.repository import ReviewRepository
from logger import logger


class ReviewService:
    def __init__(self, review_repo: Optional[ReviewRepository] = None):
        self.review_repo = review_repo or ReviewRepository()

    def get_product_rating(self, product_id: int) -> Dict[str, Any]:
        """Returns average customer rating and review count for a single product ID."""
        logger.info(f"Retrieving rating for product_id: {product_id}")
        return self.review_repo.get_product_rating(product_id)

    def get_ratings_for_products(self, product_ids: List[int]) -> List[Dict[str, Any]]:
        """Returns ratings for a batch of product IDs."""
        logger.info(f"Retrieving batch ratings for product_ids: {product_ids}")
        return self.review_repo.get_ratings_for_products(product_ids)
