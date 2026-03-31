from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.restaurant import RestaurantSchema
from app.schemas.menu import MenuSchema


class RecommendationSchema(BaseModel):
    model_config = {"from_attributes": True}
    
    restaurant: RestaurantSchema = Field(..., description="Restaurant being recommended")

    recommended_items: List[MenuSchema] = Field(
        default_factory=list,
        description="Short list of recommended menu items from the restaurant"
    )

    match_score: Optional[float] = Field(
        default=None,
        ge=0,
        description="A number showing how well this restaurant or its items match the user's preferences"
    )

    reason: Optional[str] = Field(
        default=None,
        description="A short explanation of why this recommendation was chosen"
    )

    spoken_response: Optional[str] = Field(
        default=None,
        description="Short spoken-friendly recommendation"
    )