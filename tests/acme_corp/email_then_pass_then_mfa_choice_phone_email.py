# --------------------------------------------------------------
# Email -> password -> MFA choice (phone/email) -> MFA code
# --------------------------------------------------------------
import time
import random

from fasthtml.common import (
    Input,
    Button,
    Label,
    Div,
    H1,
    Span,
    Strong,
    Fieldset,
)
from tests.acme_corp.acme_corp import app
from tests.acme_corp.constants import (
    VALID_EMAIL,
    VALID_PASSWORD,
    MIN_TIME_DELAY,
    MAX_TIME_DELAY,
)
from tests.acme_corp.helpers import render_form, email_fields, welcome_page


@app.get("/auth/email-then-password-then-mfa-choice-phone-email")
def show_email_form():
    return render_form(
        fields=email_fields,
        action="/auth/email-then-password-then-mfa-choice-phone-email",
    )


@app.post("/auth/email-then-password-then-mfa-choice-phone-email")
def handle_email(email: str):
    time.sleep(random.uniform(MIN_TIME_DELAY, MAX_TIME_DELAY))

    if email != VALID_EMAIL:
        return render_form(
            email_fields,
            "/auth/email-then-password-then-mfa-choice-phone-email",
            error_message="Unknown email",
        )

    password_fields = [
        Input(type="hidden", name="email", value=email),
        Label(
            "Password:",
            Input(
                type="password",
                name="password",
                autofocus=True,
                required=True,
            ),
        ),
        Button("Continue", type="submit"),
    ]
    return render_form(
        password_fields,
        "/submit/email-then-password-then-mfa-choice-phone-email/password",
    )


@app.post("/submit/email-then-password-then-mfa-choice-phone-email/password")
def handle_password(email: str, password: str):
    time.sleep(random.uniform(MIN_TIME_DELAY, MAX_TIME_DELAY))

    if password != VALID_PASSWORD:
        return render_form(
            [
                Input(type="hidden", name="email", value=email),
                Label(
                    "Password:",
                    Input(
                        type="password",
                        name="password",
                        autofocus=True,
                        required=True,
                    ),
                ),
                Button("Continue", type="submit"),
            ],
            "/submit/email-then-password-then-mfa-choice-phone-email/password",
            error_message="Incorrect password",
        )

    mfa_choice_fields = [
        Input(type="hidden", name="email", value=email),
        Input(type="hidden", name="password", value=password),
        H1("Let us know it's you"),
        Div(
            Span(
                "To help keep your account safe from unwanted access, "
                "we'll send you a code to verify."
            ),
            class_="dls-ihm460",
        ),
        Div(
            Strong("How should we send your code?"),
            class_="dls-ihm460",
        ),
        Fieldset(
            Label(
                Input(
                    type="radio",
                    name="delivery_method",
                    value="EMAIL",
                    checked=True,
                ),
                Div(
                    Div("Email"),
                    Div(Strong("t*****@getgather.com")),
                ),
                class_="PJmZx hktBJ",
            ),
            Label(
                Input(
                    type="radio",
                    name="delivery_method",
                    value="SMS",
                ),
                Div(
                    Div("Text message"),
                    Div(Strong("(6**) ***-8093")),
                    Div(
                        Span(
                            "Messaging and data rates may apply",
                            class_="sVKpT",
                        ),
                    ),
                ),
                class_="PJmZx YKZZh hktBJ",
            ),
            name="delivery_method",
            value="EMAIL",
            class_="YKZZh",
        ),
        Button("Send Code", type="submit", class_="dls-h9r2id")
    ]

    return render_form(
        mfa_choice_fields,
        "/submit/email-then-password-then-mfa-choice-phone-email/mfa-choice",
    )


@app.post("/submit/email-then-password-then-mfa-choice-phone-email/mfa-choice")
def handle_mfa_choice(
    email: str, password: str, delivery_method: str
):
    time.sleep(random.uniform(MIN_TIME_DELAY, MAX_TIME_DELAY))
    mfa_code_fields = [
        Input(type="hidden", name="email", value=email),
        Input(type="hidden", name="password", value=password),
        Input(type="hidden", name="delivery_method", value=delivery_method),
        H1("Enter your code to sign in"),
        Div(
            Span("This helps keep your account safe from unwanted access."),
            class_="dls-ihm460",
        ),
        Div(
            "We sent a code to:",
            Div(
                Strong("(6**) ***-8093" if delivery_method == "SMS" else "t*****@getgather.com"),
            ),
            class_="dls-ihm460",
        ),
        Label(
            Span(
                Div("Enter your code", class_="vaxnR"),
                class_="jfXvu",
            ),
            Input(
                type="text",
                name="otp",
                maxlength="40",
                pattern="[0-9]*",
                autocomplete="one-time-code",
                inputmode="numeric",
                required=True,
                autofocus=True,
            ),
            class_="mRXdL A5Ab9 Ae4rH dls-nrrlk3",
        ),
        Button("Verify and Sign in", type="submit"),
    ]
    return render_form(
        mfa_code_fields,
        "/submit/email-then-password-then-mfa-choice-phone-email/otp",
    )


@app.post("/submit/email-then-password-then-mfa-choice-phone-email/otp")
def handle_otp(
    email: str,
    password: str,
    delivery_method: str,
    otp: str,
):
    time.sleep(random.uniform(MIN_TIME_DELAY, MAX_TIME_DELAY))

    valid_code = "654321" if delivery_method == "EMAIL" else "123456"
    if (
        otp == valid_code
        and email == VALID_EMAIL
        and password == VALID_PASSWORD
    ):
        return welcome_page(email)

    mfa_code_fields = [
        Input(type="hidden", name="email", value=email),
        Input(type="hidden", name="password", value=password),
        Input(type="hidden", name="delivery_method", value=delivery_method),
        H1("Enter your code to sign in"),
        Div(
            Span("This helps keep your account safe from unwanted access."),
            class_="dls-ihm460",
        ),
        Div(
            "We sent a code to:",
            Div(
                Strong(
                    "(6**) ***-8093" if delivery_method == "SMS"
                    else "t*****@getgather.com"
                ),
            ),
            class_="dls-ihm460",
        ),
        Label(
            Span(
                Div("Enter your code", class_="vaxnR"),
                class_="jfXvu",
            ),
            Input(
                type="text",
                name="otp",
                maxlength="40",
                pattern="[0-9]*",
                autocomplete="one-time-code",
                inputmode="numeric",
                required=True,
                autofocus=True,
            ),
            class_="mRXdL A5Ab9 Ae4rH dls-nrrlk3",
        ),
        Button("Verify and Sign in", type="submit"),
    ]
    return render_form(
        mfa_code_fields,
        "/submit/email-then-password-then-mfa-choice-phone-email/otp",
        error_message="Invalid code",
    )
