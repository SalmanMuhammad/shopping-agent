from typing import Optional, Dict
from pydantic import BaseModel, Field


class Product(BaseModel):
    id: int
    name: str
    category: str
    price: float
    description: str
    is_organic: bool


class RatingInfo(BaseModel):
    product_id: int
    average_rating: float
    review_count: int


class UserPreference(BaseModel):
    prefer_organic: Optional[bool] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None


class CategoryPreferencesResponse(BaseModel):
    global_prefs: UserPreference = Field(..., alias="global")
    categories: Dict[str, UserPreference]


class Order(BaseModel):
    order_id: int
    product_name: str
    price: float
    ordered_at: str


class VisionAnalysisResult(BaseModel):
    product_type: Optional[str] = None
    search_query: str
    is_organic: Optional[bool] = None
    description: str
