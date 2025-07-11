from pydantic import BaseModel, Field

from getgather.api.types import RequestInfo
from getgather.auth_orchestrator import AuthStatus
from getgather.extract_orchestrator import ExtractState
from getgather.flow_state import FlowState
from getgather.parse import BundleOutput


class AuthFlowRequest(BaseModel):
    """Request for an auth flow."""

    profile_id: str | None = Field(
        description="The browser profile ID used for the extraction.", default=None
    )
    state: FlowState | None = Field(description="The state of the auth flow.", default=None)
    extract: bool = Field(
        default=True,
        description="Whether to extract the data after the auth flow is complete.",
    )
    location: RequestInfo | None = Field(
        description="The location for the client making the request.",
        default=None,
    )


class ExtractResult(BaseModel):
    """Result of an extract flow."""

    profile_id: str = Field(description="The browser profile ID used for the extraction.")
    state: ExtractState = Field(
        description="The state of the extract flow.",
    )
    bundles: list[BundleOutput] = Field(
        description="The file bundles and their contents that were extracted.",
    )


class AuthFlowResponse(BaseModel):
    """Response from an auth flow step."""

    profile_id: str = Field(description="The browser profile ID used for the extraction.")
    status: AuthStatus = Field(description="The status of the auth flow.")
    state: FlowState = Field(description="The state of the auth flow.")
    extract_result: ExtractResult | None = Field(
        default=None,
        description="The result of the extract flow, if one occurs.",
    )
