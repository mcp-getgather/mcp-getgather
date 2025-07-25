# ---------------------------------------------------------------------------
# Email + password -> MFA
# ---------------------------------------------------------------------------

import time
import random

from fasthtml.common import (
    Input,
    Button,
    Label,
)
from tests.acme_corp.acme_corp import app
from tests.acme_corp.constants import (
    VALID_EMAIL,
    VALID_PASSWORD,
    VALID_OTP,
    MIN_TIME_DELAY,
    MAX_TIME_DELAY,
)
from tests.acme_corp.helpers import (
    render_form,
    welcome_page,
    create_email_password_form,
)


@app.get("/auth/email-and-password-then-mfa")
def ep_pw_mfa_login_form():
    """Login form that requires email + password and then asks for MFA."""
    return create_email_password_form(action="/auth/email-and-password-then-mfa")


@app.post("/auth/email-and-password-then-mfa")
def ep_pw_mfa_login(email: str, password: str):
    """Handle the login submission and then require MFA."""
    time.sleep(random.uniform(MIN_TIME_DELAY, MAX_TIME_DELAY))

    credentials_ok = email == VALID_EMAIL and password == VALID_PASSWORD

    if not credentials_ok:
        error_msg = "You have entered an invalid email or password"
        return create_email_password_form(error_message=error_msg, action="/auth/email-and-password-then-mfa")

    return create_mfa_form(email, password)


@app.post("/submit/email-and-password-then-mfa/otp")
def ep_pw_mfa_otp(email: str, password: str, otp: str):
    """Verify the one-time code for the email + password then MFA flow."""
    time.sleep(random.uniform(MIN_TIME_DELAY, MAX_TIME_DELAY))

    creds_ok = (
        otp == VALID_OTP
        and email == VALID_EMAIL
        and password == VALID_PASSWORD
    )

    if creds_ok:
        return welcome_page(email)

    return create_mfa_form(email, password, error_message="Invalid code")

def create_mfa_form(email: str, password: str, error_message: str | None = None):
    """Create the MFA form."""
    otp_fields = [
        Input(type="hidden", name="email", value=email),
        Input(type="hidden", name="password", value=password),
        Label(
            "One-time code:",
            Input(
                type="text",
                name="otp",
                autofocus=True,
                autocomplete="one-time-code",
                required=True,
            ),
        ),
        Button("Verify", type="submit"),
    ]
    return render_form(
        otp_fields,
        "/submit/email-and-password-then-mfa/otp",
        error_message=error_message,
    )