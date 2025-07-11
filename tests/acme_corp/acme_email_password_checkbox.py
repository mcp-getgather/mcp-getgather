# ---------------------------------------------------------------------------
# Email + password with checkbox
# ---------------------------------------------------------------------------

import random
import time

from tests.acme_corp.acme_corp import app
from tests.acme_corp.constants import (
    MAX_TIME_DELAY,
    MIN_TIME_DELAY,
    VALID_EMAIL,
    VALID_PASSWORD,
)
from tests.acme_corp.helpers import create_email_password_form, welcome_page


@app.get("/auth/email-and-password-checkbox")
def login_form():
    return create_email_password_form(
        action="/submit/email-and-password-checkbox", show_remember_me=True
    )


@app.post("/submit/email-and-password-checkbox")
def login_submit(email: str, password: str, remember_me: bool = False):
    time.sleep(random.uniform(MIN_TIME_DELAY, MAX_TIME_DELAY))

    if email == VALID_EMAIL and password == VALID_PASSWORD and remember_me:
        return welcome_page(email)

    return create_email_password_form(
        "You have entered an invalid email or password, or you did not check the remember me checkbox",
        action="/submit/email-and-password-checkbox",
        show_remember_me=True,
    )
