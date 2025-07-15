# ---------------------------------------------------------------------------
# Email -> password
# ---------------------------------------------------------------------------
import random
import time

from fasthtml.common import (
    H1,
    Body,
    Button,
    Head,
    Html,
    Input,
    Label,
    Main,
    P,
    Title,
    picolink,
)

from tests.acme_corp.acme_corp import app
from tests.acme_corp.constants import (
    MAX_TIME_DELAY,
    MIN_TIME_DELAY,
    VALID_EMAIL,
    VALID_PASSWORD,
)
from tests.acme_corp.helpers import (
    create_email_form,
    create_password_form,
    handle_email_validation,
    password_form_callback,
    welcome_page,
)


@app.get("/auth/email-then-password")
def email_form():
    # First page: email entry; form submits back to the same /auth route.
    return create_email_form(action="/auth/email-then-password")


@app.post("/auth/email-then-password")
def check_email(email: str):
    return handle_email_validation(
        email,
        error_form_action="/auth/email-then-password",
        error_message="Unrecognized email",
        success_callback=password_form_callback("/submit/email-then-password/login"),
        use_random_delay=True,
    )


@app.post("/submit/email-then-password/login")
def check_password(email: str, password: str):
    time.sleep(random.uniform(MIN_TIME_DELAY, MAX_TIME_DELAY))

    if email == VALID_EMAIL and password == VALID_PASSWORD:
        return welcome_page(email)

    return create_password_form(
        email, "Incorrect credentials", action="/submit/email-then-password/login"
    )
