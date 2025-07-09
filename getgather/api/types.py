from typing import TypedDict
from contextvars import ContextVar
from pydantic import BaseModel, Field


class Location(TypedDict):
    city: str | None
    state: str | None
    country: str | None
    postal_code: str | None

class RequestInfo(BaseModel):
    """Information about the request that initiated the auth flow."""
    city: str | None = Field(description="The city of the client.", default=None)
    state: str | None = Field(description="The state of the client.", default=None)
    country: str | None = Field(description="The country of the client.", default=None)
    postal_code: str | None = Field(description="The postal code of the client.", default=None)


request_info: ContextVar[RequestInfo | None] = ContextVar("request_info", default=None)
