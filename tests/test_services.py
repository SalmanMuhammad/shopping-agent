import os
import tempfile
from pathlib import Path
from database.setup import init_db
from database.repository import (
    ProductRepository,
    ReviewRepository,
    OrderRepository,
    PreferenceRepository,
)
from services.product_service import ProductService
from services.review_service import ReviewService
from services.order_service import OrderService
from services.preference_service import PreferenceService




def test_product_search_and_preferences(temp_db):
    product_repo = ProductRepository(temp_db)
    pref_repo = PreferenceRepository(temp_db)
    product_service = ProductService(product_repo, pref_repo)
    pref_service = PreferenceService(pref_repo)

    # Search without preference
    products = product_service.search_products(query="honey")
    assert len(products) > 0

    # Set organic preference for honey
    pref_service.set_preferences(category="honey", prefer_organic=True)
    organic_honey = product_service.search_products(query="honey", category="honey")
    for p in organic_honey:
        assert p["is_organic"] is True


def test_review_service(temp_db):
    review_repo = ReviewRepository(temp_db)
    review_service = ReviewService(review_repo)

    rating = review_service.get_product_rating(product_id=1)
    assert rating["product_id"] == 1
    assert rating["average_rating"] > 0
    assert rating["review_count"] > 0


def test_order_service(temp_db):
    order_repo = OrderRepository(temp_db)
    product_repo = ProductRepository(temp_db)
    order_service = OrderService(order_repo, product_repo)

    # Checkout product 1
    confirmation = order_service.checkout(product_id=1)
    assert "confirmed!" in confirmation

def run_all_service_tests():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = Path(tmp.name)
    try:
        init_db(db_path)
        test_product_search_and_preferences(db_path)
        print("✅ test_product_search_and_preferences passed")
        test_review_service(db_path)
        print("✅ test_review_service passed")
        test_order_service(db_path)
        print("✅ test_order_service passed")
        print("\n🎉 All domain service unit tests passed successfully!")
    finally:
        if db_path.exists():
            os.remove(db_path)


if __name__ == "__main__":
    run_all_service_tests()

