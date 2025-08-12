from pydantic import BaseModel, Field


class UpdateBrandEnabledRequest(BaseModel):
    enabled: bool = Field(description="Whether the brand is enabled")
