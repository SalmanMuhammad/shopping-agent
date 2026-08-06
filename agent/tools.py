import json
from typing import Optional, Union
from langchain.tools import tool

from services.product_service import ProductService
from services.review_service import ReviewService
from services.order_service import OrderService
from services.preference_service import PreferenceService
from services.vision_service import VisionService

# Singleton service instances
product_service = ProductService()
review_service = ReviewService()
order_service = OrderService()
preference_service = PreferenceService()
vision_service = VisionService()


@tool
def search_products(
    query: str,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    is_organic: Optional[Union[bool, str]] = None,
    category: Optional[str] = None,
) -> str:
    """
    Search the product database by keyword (matched against name, description, and category).
    If max_price, min_price or is_organic are not provided,
    If category is provided, load category-specific preference.
    Returns a JSON array of matching products, each with: id, name, category, price,
    description, is_organic.
    """
    products = product_service.search_products(
        query=query,
        min_price=min_price,
        max_price=max_price,
        is_organic=is_organic,
        category=category,
    )
    return json.dumps(products)


@tool
def get_rating(product_id: int) -> str:
    """
    Get the average customer rating and total review count for a product_id.
    ARGUMENT: 'product_id' (integer) - the exact product ID from the search results.
    You MUST pass this argument with the name 'product_id' (e.g., get_rating(product_id=25)).
    Returns a JSON object with: product_id, average_rating, review_count.
    """
    rating_info = review_service.get_product_rating(product_id=product_id)
    return json.dumps(rating_info)


@tool
def checkout(product_id: int) -> str:
    """
    Place an order for the given product ID. Saves the order to the database and returns
    a confirmation message with the order ID, product name, and price.
    """
    return order_service.checkout(product_id=product_id)


@tool
def get_order_history(
    limit: Optional[int] = 10,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> str:
    """
    Get a summary of the user's order history.
    Returns a JSON array of orders with: order_id, product_name, price, ordered_at.
    Can filter by date range and limit the number of results.
    """
    orders = order_service.get_order_history(
        limit=limit, start_date=start_date, end_date=end_date
    )
    return json.dumps(orders)


@tool
def describe_product_image(image_path: str) -> str:
    """
    Analyze a product image and return its key attributes as a JSON object.
    Use this when the user uploads a photo of a product they are interested in.
    The returned attributes can be used directly with search_products.
    """
    return vision_service.describe_product_image(image_path=image_path)


@tool
def set_preferences(
    category: Optional[str] = None,
    prefer_organic: Optional[bool] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> str:
    """Set preferences for a category or globally."""
    return preference_service.set_preferences(
        category=category,
        prefer_organic=prefer_organic,
        min_price=min_price,
        max_price=max_price,
    )


@tool
def get_preferences(category: Optional[str] = None) -> str:
    """
    Get preferences. If category is given, return that category's preferences.
    If no category, return all (global + every category).
    """
    prefs = preference_service.get_preferences(category=category)
    return json.dumps(prefs)


tools = [
    search_products,
    get_rating,
    checkout,
    describe_product_image,
    get_order_history,
    set_preferences,
    get_preferences,
]
