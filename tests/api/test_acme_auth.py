import os
from typing import Any

import pytest
import requests

HOST = os.environ.get("HOST", "http://localhost:8000")
API_KEY = os.environ.get("API_KEY")

ACME_TEST_CASES = [
    # Simple tests
    {"test": "acme-email-password-checkbox"},
    
]


def get_test_id(test_case: dict[str, str]):
    """Generate a unique ID for each test case for better test reporting."""
    parts = [test_case["test"]]
    if "verification_choice" in test_case:
        parts.append(f"vc_{test_case['verification_choice']}")
    if "mfa_choice" in test_case:
        parts.append(f"mc_{test_case['mfa_choice']}")
    return "-".join(parts)


@pytest.mark.api
@pytest.mark.acme
@pytest.mark.parametrize(
    "test_case", ACME_TEST_CASES, ids=[get_test_id(tc) for tc in ACME_TEST_CASES]
)
def test_acme_auth_flow(test_case: dict[str, str]):
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
                    inputs[prompt_name] = os.environ.get("ACME_EMAIL", "joe@example.com")
                elif prompt_name == "password":
                    inputs[prompt_name] = os.environ.get("ACME_PASSWORD", "trustno1")
                elif prompt_name == "lastname":
                    inputs[prompt_name] = os.environ.get("ACME_LASTNAME", "Sixpack")
                elif prompt_name == "otp":
                    inputs[prompt_name] = os.environ.get("ACME_OTP", "123456")
                elif prompt_name == "mfa_code":
                    # Use the correct MFA code based on the choice
                    mfa_choice = test_case.get("mfa_choice")
                    if mfa_choice == "email":
                        inputs[prompt_name] = "654321"
                    elif mfa_choice == "phone":
                        inputs[prompt_name] = "654321"
                    else:
                        inputs[prompt_name] = os.environ.get("ACME_MFA_CODE", "123456")

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
