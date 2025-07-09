import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from getgather.config import settings


class LoginAttemptProperties(BaseModel):
    brand_id: str = Field(description="The brand ID of the brand being extracted")
    login_status: str = Field(
        description="Result of the login attempt. Mimics the AuthStatus enum."
    )
    auth_state: dict[str, Any] = Field(
        default_factory=dict,
        description="The state of the auth flow. Mimics the AuthState class.",
    )

    @field_validator("auth_state", mode="before")
    @classmethod
    def clean_auth_state(cls, auth_state: dict[str, Any]) -> dict[str, Any]:
        # Clean up the auth_state["inputs"] dictionary to remove all values except for "email" and "username"
        # TODO: A cleaner and more robust solution would be to have the Brand Spec (YAML) define certain fields as sensitive so we can hide them with quick filtering
        cleaned_auth_state = auth_state.copy()
        inputs_value: dict[str, str] = cleaned_auth_state.get("inputs", {})
        new_sanitized_inputs: dict[str, str] = {}
        for key, value in inputs_value.items():
            if key not in ["email", "username"]:
                new_sanitized_inputs[key] = "********"
            else:
                new_sanitized_inputs[key] = value
            cleaned_auth_state["inputs"] = new_sanitized_inputs

        return cleaned_auth_state


class ExtractStepProperties(BaseModel):
    brand_id: str = Field(description="The brand ID of the brand being extracted")
    extract_status: str = Field(
        description="The state of the extract flow. Mimics the ExtractState enum."
    )
    parsing_status: Literal["not_used", "success", "failure"] = Field(
        description="Status of data parsing"
    )
    num_orders: int | None = Field(description="Number of orders processed", default=None)


EventPayload = LoginAttemptProperties | ExtractStepProperties | dict[str, Any]


class Event(BaseModel):
    # Derived Fields
    timestamp: datetime = Field(init=False, default_factory=lambda: datetime.now(UTC))
    event_id: str = Field(init=False, default_factory=lambda: str(uuid.uuid4()))

    # Passed in from the caller
    profile_id: str = Field(description="The browser profile ID used for the extraction.")
    event_name: Literal[
        "page_view", "user_action", "login_attempt", "extract_step", "parse_step"
    ] = Field(description="The name of the event being tracked")
    event_payload: EventPayload


class Attributes(BaseModel):
    environment: str = Field(default=settings.ENVIRONMENT)
    app_name: str = Field(default=settings.APP_NAME)


async def send_analytics_event(event: Event, attributes: Attributes = Attributes()):
    return
