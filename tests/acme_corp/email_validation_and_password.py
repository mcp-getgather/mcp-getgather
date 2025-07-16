# ---------------------------------------------------------------------------
# Email validation and password
# ---------------------------------------------------------------------------
import random
import time

from fasthtml.common import (
    H1,
    Body,
    Head,
    Html,
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
    create_email_password_form,
    welcome_page,
)


@app.get("/auth/email-validation-and-password")
def login_form():
    return create_email_password_form(show_remember_me=False, email_validation=True)


@app.post("/submit/email-validation-and-password")
def login_submit(email: str, password: str):
    if email == VALID_EMAIL and password == VALID_PASSWORD:
        return welcome_page(email)

    return create_email_password_form(
        "You have entered an invalid email or password", show_remember_me=False
    )
