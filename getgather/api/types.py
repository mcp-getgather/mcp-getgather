from contextvars import ContextVar

from pydantic import BaseModel, Field


class RequestInfo(BaseModel):
    """Information about the request that initiated the auth flow."""

    city: str | None = Field(description="The city of the client.", default=None)
    state: str | None = Field(description="The state of the client.", default=None)
    country: str | None = Field(description="The country of the client.", default=None)
    postal_code: str | None = Field(description="The postal code of the client.", default=None)
    custom_proxy_username: str | None = Field(
        description="Optional custom proxy username supplied by the client header.",
        default=None,
    )


request_info: ContextVar[RequestInfo | None] = ContextVar("request_info", default=None)
