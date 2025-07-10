import os
from typing import Any

import pytest
import requests

HOST = os.environ.get("HOST", "http://localhost:8000")
API_KEY = os.environ.get("API_KEY")

TEST_CASES = [
    # Simple tests
    {"test": "cnn"},
    
]


def get_test_id(test_case: dict[str, str]):
    """Generate a unique ID for each test case for better test reporting."""
    parts = [test_case["test"]]
    if "verification_choice" in test_case:
        parts.append(f"vc_{test_case['verification_choice']}")
    if "mfa_choice" in test_case:
        parts.append(f"mc_{test_case['mfa_choice']}")
    return "-".join(parts)


@pytest.mark.parametrize(
    "test_case", TEST_CASES, ids=[get_test_id(tc) for tc in TEST_CASES]
)
def test_auth_api_flow(test_case: dict[str, str]):
    brand_id = test_case["test"]
    headers: dict[str, str] = {}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"

    # 1. Start the auth flow
    initial_payload = {"extract": True}
    res = requests.post(
        f"{HOST}/auth/{brand_id}", json=initial_payload, headers=headers, timeout=120
    )
    res.raise_for_status()
    data: dict[str, Any] = res.json()

    profile_id = data.get("profile_id")
    state = data.get("state")

    assert profile_id, f"Failed to get profile_id from initial response for {brand_id}"
    assert state, f"Failed to get state from initial response for {brand_id}"

    # 2. Loop until the flow is finished
    while data.get("status") != "FINISHED":
        prompt = state.get("prompt")
        inputs: dict[str, str] = {}

        if prompt and prompt.get("choices"):
            # Only process the first choice group (like CLI does one step at a time)
            choice = prompt["choices"][0]
            # Set the choice value for the group name if it exists in test case (like CLI does)
            if choice.get("name") and choice.get("name") in test_case:
                inputs[choice["name"]] = test_case[choice["name"]]
            # Only send fields present in the current prompt group
            for p in choice.get("prompts", []):
                prompt_name = p.get("name")
                if not prompt_name:
                    continue
                # Handle click-type prompts (always set to "true")
                if p.get("type") == "click":
                    inputs[prompt_name] = "true"
                # Handle specific field types
                elif prompt_name == "email":
                    inputs[prompt_name] = os.environ.get("CNN_USERNAME", "")
                elif prompt_name == "password":
                    inputs[prompt_name] = os.environ.get("CNN_PASSWORD", "")

        state["inputs"] = inputs
        state["inputs"]["submit"] = "true"

        payload = {"profile_id": profile_id, "state": state, "extract": True}
        res = requests.post(f"{HOST}/auth/{brand_id}", json=payload, headers=headers, timeout=120)
        res.raise_for_status()
        data = res.json()
        state = data["state"]

    # 3. Final assertions
    assert data.get("status") == "FINISHED", f"Flow did not finish for {brand_id}"
    if brand_id != "universal-error-page":
        assert state.get("error") is None, (
            f"Flow finished with error for {brand_id}: {state.get('error')}"
        )
    else:
        assert (
            state.get("error") == "❌ Test error page detected. This is a universal test error."
        ), (
            f"Expected an error message but didn't get one that matched for {brand_id}. Got {state.get('error')}"
        )
