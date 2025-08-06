# --------------------------------------------------------------
# Email -> password -> MFA
# --------------------------------------------------------------
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
from tests.acme_corp.helpers import email_fields, render_form, welcome_page


@app.get("/auth/email-then-password-then-mfa")
def show_email_form():
    return render_form(
        fields=email_fields,
        action="/submit/email-then-password-then-mfa/email",
    )


@app.post("/submit/email-then-password-then-mfa/email")
def handle_email(email: str):
    time.sleep(random.uniform(MIN_TIME_DELAY, MAX_TIME_DELAY))

    if email != VALID_EMAIL:
        return render_form(
            email_fields,
            "/submit/email-then-password-then-mfa/email",
            error_message="Unknown email",
        )

    password_fields = [
        Input(type="hidden", name="email", value=email),
        Label("Password:", Input(type="password", name="password", autofocus=True, required=True)),
        Button("Continue", type="submit"),
    ]
    return render_form(password_fields, "/submit/email-then-password-then-mfa/password")


@app.post("/submit/email-then-password-then-mfa/password")
def handle_password(email: str, password: str):
    time.sleep(random.uniform(MIN_TIME_DELAY, MAX_TIME_DELAY))

    if password != VALID_PASSWORD:
        return render_form(
            [
                Input(type="hidden", name="email", value=email),
                Label(
                    "Password:",
                    Input(type="password", name="password", autofocus=True, required=True),
                ),
                Button("Continue", type="submit"),
            ],
            "/submit/email-then-password-then-mfa/password",
            button="Continue",
            error_message="Incorrect password",
        )

    mfa_fields = [
        Input(type="hidden", name="email", value=email),
        Input(type="hidden", name="password", value=password),
        Label(
            "One-time code:",
            Input(
                type="text", name="otp", autofocus=True, autocomplete="one-time-code", required=True
            ),
        ),
        Button("Verify", type="submit"),
    ]
    return render_form(mfa_fields, "/submit/email-then-password-then-mfa/otp")


@app.post("/submit/email-then-password-then-mfa/otp")
def handle_otp(email: str, password: str, otp: str):
    time.sleep(random.uniform(MIN_TIME_DELAY, MAX_TIME_DELAY))

    if otp == VALID_OTP and email == VALID_EMAIL and password == VALID_PASSWORD:
        return welcome_page(email)

    mfa_fields = [
        Input(type="hidden", name="email", value=email),
        Input(type="hidden", name="password", value=password),
        Label(
            "One-time code:",
            Input(
                type="text", name="otp", autofocus=True, autocomplete="one-time-code", required=True
            ),
        ),
    ]
    return render_form(
        mfa_fields,
        "/submit/email-then-password-then-mfa/otp",
        button="Verify",
        error_message="Invalid code",
    )
