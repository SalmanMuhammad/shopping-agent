from typing import Optional, List, Dict, Any, Union
from database.repository import ProductRepository, PreferenceRepository
from logger import logger


class ProductService:
    def __init__(
        self,
        product_repo: Optional[ProductRepository] = None,
        pref_repo: Optional[PreferenceRepository] = None,
    ):
        self.product_repo = product_repo or ProductRepository()
        self.pref_repo = pref_repo or PreferenceRepository()

    def search_products(
        self,
        query: str,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        is_organic: Optional[Union[bool, str]] = None,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Searches products matching the query.
        Applies category or global stored preferences if explicit parameters are None.
        """
        if isinstance(is_organic, str):
            if is_organic.lower() in ("true", "1", "yes"):
                is_organic = True
            elif is_organic.lower() in ("false", "0", "no"):
                is_organic = False
            else:
                is_organic = None

        prefs = self.pref_repo.get_user_preferences(category)

        # Apply stored preferences if explicit parameter is not passed
        if min_price is None and prefs.get("min_price") is not None:
            min_price = prefs["min_price"]
        if max_price is None and prefs.get("max_price") is not None:
            max_price = prefs["max_price"]
        if is_organic is None and prefs.get("prefer_organic") is not None:
            is_organic = prefs["prefer_organic"]

        logger.info(
            f"Executing product search — Query: '{query}', Category: {category}, "
            f"MinPrice: {min_price}, MaxPrice: {max_price}, Organic: {is_organic}"
        )

        return self.product_repo.search_products(
            query=query,
            min_price=min_price,
            max_price=max_price,
            is_organic=is_organic,
        )

    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        return self.product_repo.get_by_id(product_id)
