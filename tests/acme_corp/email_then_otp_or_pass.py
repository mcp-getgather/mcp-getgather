# ---------------------------------------------------------------------------
# Email -> OTP/Password choice
# ---------------------------------------------------------------------------

import random
import time

from fasthtml.common import (
    Button,
    Input,
    Label,
)

from tests.acme_corp.acme_corp import app
from tests.acme_corp.constants import (
    MAX_TIME_DELAY,
    MIN_TIME_DELAY,
    VALID_EMAIL,
    VALID_OTP,
    VALID_PASSWORD,
)
from tests.acme_corp.helpers import (
    create_email_form,
    create_otp_form,
    create_password_form,
    handle_email_validation,
    render_form,
    welcome_page,
)


@app.get("/auth/email-then-otp-or-password")
def email_then_otp_or_password_form():
    """Initial login form that asks for email."""
    return create_email_form(action="/auth/email-then-otp-or-password")


def create_otp_or_password_form(email: str, error_message: str = None):
    """Create a form with password input and options to use OTP instead."""
    password_fields = [
        Input(type="hidden", name="email", value=email),
        Label(
            "One time code:",
            Input(
                type="text",
                name="otp",
                # Password only required for login button
                required=False,
            ),
        ),
        Button(
            "Log in",
            type="submit",
            formaction="/submit/email-then-otp-or-password/otp",
            # Add form validation for OTP code on this button
            onclick=(
                "if(!this.form.otp.value) { event.preventDefault(); "
                "this.form.otp.required = true; "
                "this.form.otp.reportValidity(); return false; }"
            ),
        ),
        Button(
            "Use a password instead",
            type="submit",
            formaction="/submit/email-then-otp-or-password/password",
        ),
    ]
    return render_form(
        password_fields,
        action="/submit/email-then-otp-or-password/otp",
        error_message=error_message,
    )


@app.post("/auth/email-then-otp-or-password")
def handle_email_submission(email: str):
    """Handle the email submission and show password page with OTP option."""
    return handle_email_validation(
        email,
        error_form_action="/auth/email-then-otp-or-password",
        error_message="Invalid email address",
        success_callback=create_otp_or_password_form,
        use_random_delay=True,
    )


@app.post("/submit/email-then-otp-or-password/password")
def handle_password_request(email: str):
    """Handle the request for OTP and show OTP input form."""
    time.sleep(random.uniform(MIN_TIME_DELAY, MAX_TIME_DELAY))
    return create_password_form(
        email,
        action="/submit/email-then-otp-or-password/verify-password",
    )


@app.post("/submit/email-then-otp-or-password/verify-password")
def handle_password_verification(email: str, password: str = None):
    """Handle the password verification step."""
    time.sleep(random.uniform(MIN_TIME_DELAY, MAX_TIME_DELAY))

    if email == VALID_EMAIL and password == VALID_PASSWORD:
        return welcome_page(email)

    error_msg = "Invalid password" if password is not None else None
    return create_otp_or_password_form(email, error_message=error_msg)


@app.post("/submit/email-then-otp-or-password/otp")
def handle_otp_verification(email: str, otp: str):
    """Handle the OTP verification step."""
    time.sleep(random.uniform(MIN_TIME_DELAY, MAX_TIME_DELAY))

    if email == VALID_EMAIL and otp == VALID_OTP:
        return welcome_page(email)

    error_msg = "Invalid code"
    return create_otp_form(
        email,
        action="/submit/email-then-otp-or-password/otp",
        error_message=error_msg,
    )
