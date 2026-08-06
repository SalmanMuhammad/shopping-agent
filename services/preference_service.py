from typing import Optional, Dict, Any
from database.repository import PreferenceRepository
from logger import logger


class PreferenceService:
    def __init__(self, pref_repo: Optional[PreferenceRepository] = None):
        self.pref_repo = pref_repo or PreferenceRepository()

    def get_preferences(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Returns preferences for a specific category or all preferences."""
        if category:
            logger.info(f"Retrieving preferences for category: {category}")
            return self.pref_repo.get_user_preferences(category)
        else:
            logger.info("Retrieving all (global + category) preferences")
            return self.pref_repo.get_all_category_preferences()

    def set_preferences(
        self,
        category: Optional[str] = None,
        prefer_organic: Optional[bool] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> str:
        """Sets preferences for a category or globally."""
        logger.info(
            f"Updating preferences — Category: {category}, Organic: {prefer_organic}, MinPrice: {min_price}, MaxPrice: {max_price}"
        )
        return self.pref_repo.set_user_preference(
            category=category,
            prefer_organic=prefer_organic,
            min_price=min_price,
            max_price=max_price,
        )
