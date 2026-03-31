from sqlalchemy import Boolean, Column, String, Text, ForeignKey, Float, ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(String, primary_key=True, index=True)
    restaurant_id = Column(String, ForeignKey("restaurants.id"), nullable=False)

    section_name = Column(String, nullable=False)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=True)

    dietary_info = Column(ARRAY(String), nullable=True)
    allergens = Column(ARRAY(String), nullable=True)
    spice_level = Column(String, nullable=True)
    tags = Column(ARRAY(String), nullable=True)

    is_available = Column(Boolean, default=True)
    short_summary = Column(Text, nullable=True)

    restaurant = relationship("Restaurant", back_populates="menu_items")