from sqlalchemy import Column, String, Float, Boolean, ARRAY, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    cuisine_type = Column(String, nullable=False)
    rating = Column(Float, nullable=True)
    price_level = Column(String, nullable=True)
    is_open = Column(Boolean, default=True)
    menu_available = Column(Boolean, default=False)
    dietary_options = Column(ARRAY(String), nullable=True)
    short_summary = Column(Text, nullable=True)

    menu_items = relationship("MenuItem", back_populates="restaurant")