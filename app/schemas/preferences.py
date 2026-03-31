from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class PreferencesSchema(BaseModel):
    cuisine_preferences: List[str] = Field(
        default_factory=list,
        description="A list of cuisines the user wants"
    )

    dietary_restrictions: List[str] = Field(
        default_factory=list,
        description="A list of dietary needs or exclusions"
    )
    
    allergen_exclusions: List[str] = Field(
        default_factory=list,
        description="A list of allergens the user wants to avoid"
    )

    spice_preference: Optional[Literal["mild", "medium", "spicy"]] = Field(
        default=None,
        description="Spice preference"
    )

    price_preference: Optional[Literal["cheap", "moderate", "expensive"]] = Field(
        default=None,
        description="Price preference"
    )

    max_travel_time_minutes: Optional[float] = Field(
        default=None,
        ge=0,
        description="Maximum travel time in minutes the user is willing to spend"
    )

    preferred_tags: List[str] = Field(
        default_factory=list,
        description="List of preferred tags for recommendation logic"
    )