from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class MenuSchema(BaseModel):
    model_config = {"from_attributes": True}
    
    id: str = Field(..., min_length=1, description="Unique identifier for the menu item")
    restaurant_id: str = Field(..., min_length=1, description="Links the item back to its restaurant")
    section_name: str = Field(..., min_length=1, description="Organizes the item by menu section")
    name: str = Field(..., min_length=1, description="Item name")

    description: Optional[str] = Field(
        default=None,
        description="Description of the menu item"
    )

    price: Optional[float] = Field(
        default=None,
        ge=0,
        description="Price of the menu item"
    )

    dietary_info: List[str] = Field(
        default_factory=list,
        description="Dietary information such as vegetarian or halal"
    )
    
    allergens: List[str] = Field(
        default_factory=list,
        description="Allergens contained in the menu item such as nuts or dairy"
    )

    spice_level: Optional[Literal["mild", "medium", "spicy", "very spicy"]] = Field(
        default=None,   
        description="Relative spice level"
    )   

    tags: List[str] = Field(
        default_factory=list,
        description="Tags used for recommendation logic such as high protein or rice"
    )

    is_available: bool = Field(
        default=True,
        description="Whether the menu item is currently available"
    )

    short_summary: Optional[str] = Field(
        default=None,
        description="Short spoken-friendly summary of the menu item"
    )