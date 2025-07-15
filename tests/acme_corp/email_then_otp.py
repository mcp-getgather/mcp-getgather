# ---------------------------------------------------------------------------
# Email -> OTP
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
    VALID_OTP,
)
from tests.acme_corp.helpers import (
    create_email_form,
    create_otp_form,
    welcome_page,
)


@app.get("/auth/email-then-otp")
def email_otp_form():
    return create_email_form(action="/auth/email-then-otp")


@app.post("/auth/email-then-otp")
def check_email_from_otp(email: str):
    time.sleep(random.uniform(MIN_TIME_DELAY, MAX_TIME_DELAY))

    if email != VALID_EMAIL:
        return create_email_form(
            "Error occurred",
            action="/auth/email-then-otp",
        )

    return create_otp_form(email, action="/submit/email-then-otp/login")


@app.post("/submit/email-then-otp/login")
def check_otp(email: str, otp: str):
    time.sleep(random.uniform(MIN_TIME_DELAY, MAX_TIME_DELAY))

    if email == VALID_EMAIL and otp == VALID_OTP:
        return welcome_page(email)

    return create_otp_form(email, "Incorrect credentials")
