from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class RestaurantSchema(BaseModel):
    model_config = {"from_attributes": True}
    
    id: str = Field(..., min_length=1, description="Unique restaurant identifier")
    name: str = Field(..., min_length=1, description="Restaurant name")
    cuisine_type: str = Field(..., min_length=1, description="Type of cuisine")

    rating: Optional[float] = Field(
        default=None,
        ge=0,
        le=5,
        description="Restaurant rating from 0 to 5"
    )

    price_level: Optional[Literal["cheap", "moderate", "expensive"]] = Field(
        default=None,
        description="Relative price level"
    )

    is_open: Optional[bool] = Field(
        default=None,
        description="Whether the restaurant is currently open"
    )

    menu_available: bool = Field(..., description="Whether menu data is available for this restaurant")

    dietary_options: List[str] = Field(
        default_factory=list,
        description="Supported dietary options such as vegan or halal"
    )
    
    travel_time_minutes: Optional[float] = Field(
        default=None,
        ge=0,
        description="Estimated travel time to the restaurant in minutes"
    )

    short_summary: Optional[str] = Field(
        default=None,
        description="Short spoken-friendly summary of the restaurant"
    )