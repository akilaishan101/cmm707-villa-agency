from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AgentBase(BaseModel):
    name: str
    email: EmailStr
    contact_number: str
    specialization: str
    assigned_property_count: int = Field(default=0, ge=0)


class AgentCreate(AgentBase):
    pass


class AgentResponse(AgentBase):
    agent_id: int

    model_config = ConfigDict(from_attributes=True)