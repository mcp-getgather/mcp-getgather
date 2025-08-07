from typing import Any

from pydantic import BaseModel, Field, field_validator


class HostedLinkTokenRequest(BaseModel):
    """Request for creating a hosted link token."""

    brand_id: str = Field(description="Brand identifier for authentication")
    redirect_url: str | None = Field(
        description="URL to redirect after successful auth", default=None
    )
    webhook: str | None = Field(description="Webhook URL for notifications", default=None)
    url_lifetime_seconds: int = Field(description="Token lifetime in seconds", default=900)
    profile_id: str | None = Field(description="Existing browser profile ID to reuse", default=None)

    @field_validator("url_lifetime_seconds")
    @classmethod
    def validate_lifetime(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("url_lifetime_seconds must be positive")
        return v


class HostedLinkTokenResponse(BaseModel):
    """Response from creating a hosted link token."""

    link_id: str = Field(description="6-character link identifier")
    # option to not return profile_id in the response
    profile_id: str | None = Field(description="Browser profile identifier", default=None)
    hosted_link_url: str = Field(description="Complete hosted link URL")
    expiration: str = Field(description="Token expiration timestamp")


class TokenLookupResponse(BaseModel):
    """Response from token lookup."""

    link_id: str = Field(description="6-character link identifier")
    profile_id: str | None = Field(description="Browser profile identifier", default=None)
    brand_id: str
    redirect_url: str | None
    webhook: str | None
    status: str
    created_at: str
    expires_at: str
    extract_result: dict[str, Any] | None = Field(
        description="Extracted authentication data", default=None
    )
    message: str
