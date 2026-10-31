from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class PropertyStatus(str, Enum):
    AVAILABLE = "Available"
    RESERVED = "Reserved"
    SOLD = "Sold"
    RENTED = "Rented"


class PropertyBase(BaseModel):
    title: str
    property_type: str
    location: str
    price: float = Field(gt=0)
    bedrooms: int = Field(ge=0)
    bathrooms: int = Field(ge=0)
    floor_area: float = Field(gt=0)
    status: PropertyStatus
    assigned_agent_id: int | None = None


class PropertyCreate(PropertyBase):
    pass


class PropertyResponse(PropertyBase):
    property_id: int

    model_config = ConfigDict(from_attributes=True)