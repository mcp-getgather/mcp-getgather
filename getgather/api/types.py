from contextvars import ContextVar

from pydantic import BaseModel, Field


class ProxyInfo(BaseModel):
    """Information about the proxy that initiated the auth flow."""

    city: str | None = Field(description="The city of the client.", default=None)
    state: str | None = Field(description="The state of the client.", default=None)
    country: str | None = Field(description="The country of the client.", default=None)
    postal_code: str | None = Field(description="The postal code of the client.", default=None)
    browser_proxy: str | None = Field(
        description="The URL of the proxy. Empty string if no proxy is used.", default=None
    )


proxy_info: ContextVar[ProxyInfo | None] = ContextVar("proxy_info", default=None)
