from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EnquiryStatus(str, Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class EnquiryBase(BaseModel):
    property_id: int = Field(gt=0)
    customer_name: str
    customer_email: EmailStr
    customer_contact: str
    viewing_datetime: datetime
    message: str = Field(min_length=1, max_length=2000)
    status: EnquiryStatus = EnquiryStatus.PENDING


class EnquiryCreate(EnquiryBase):
    pass


class EnquiryResponse(EnquiryBase):
    enquiry_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
