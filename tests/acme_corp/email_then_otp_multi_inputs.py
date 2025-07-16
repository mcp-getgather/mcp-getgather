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
    handle_email_validation,
    welcome_page,
)


@app.get("/auth/email-then-otp-multi-inputs")
def email_otp_form():
    return create_email_form(action="/auth/email-then-otp-multi-inputs")


@app.post("/auth/email-then-otp-multi-inputs")
def check_email_from_otp(email: str):
    return handle_email_validation(
        email,
        error_form_action="/auth/email-then-otp-multi-inputs",
        error_message="Invalid email address",
        success_callback=lambda email: create_otp_form(
            email, action="/submit/email-then-otp-multi-inputs/login", multi_inputs=True
        ),
        use_random_delay=True,
    )


@app.post("/submit/email-then-otp-multi-inputs/login")
def check_otp(email: str, otp: str):
    time.sleep(random.uniform(MIN_TIME_DELAY, MAX_TIME_DELAY))

    if email == VALID_EMAIL and otp == VALID_OTP:
        return welcome_page(email)

    return create_otp_form(email, "Incorrect credentials")
