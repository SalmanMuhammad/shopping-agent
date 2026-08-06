from typing import Optional, List, Dict, Any
from database.repository import OrderRepository, ProductRepository
from logger import logger


class OrderService:
    def __init__(
        self,
        order_repo: Optional[OrderRepository] = None,
        product_repo: Optional[ProductRepository] = None,
    ):
        self.order_repo = order_repo or OrderRepository()
        self.product_repo = product_repo or ProductRepository()

    def checkout(self, product_id: int) -> str:
        """Places an order for the product with product_id."""
        logger.info(f"Initiating checkout for product_id: {product_id}")
        product = self.product_repo.get_by_id(product_id)
        if not product:
            logger.warning(f"Checkout failed: Product ID {product_id} not found.")
            return f"Error: product with ID {product_id} not found."

        name = product["name"]
        price = product["price"]
        order_id = self.order_repo.create_order(product_id, name, price)
        logger.info(f"Order #{order_id} created for '{name}' (${price:.2f}).")

        return (
            f"Order #{order_id} confirmed! '{name}' has been successfully ordered for ${price:.2f}. "
            f"Your order will arrive in 3-5 business days. Thank you for shopping with us!"
        )

    def get_order_history(
        self,
        limit: Optional[int] = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves user order history."""
        logger.info(f"Fetching order history (limit={limit}, start={start_date}, end={end_date})")
        return self.order_repo.get_orders(limit=limit, start_date=start_date, end_date=end_date)
