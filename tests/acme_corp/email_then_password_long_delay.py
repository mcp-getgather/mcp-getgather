# ---------------------------------------------------------------------------
# Email -> password
# ---------------------------------------------------------------------------
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


@app.get("/auth/email-then-password-long-delay")
def email_form():
    # Display initial email form; post back to the same /auth route.
    return create_email_form(action="/auth/email-then-password-long-delay")


@app.post("/auth/email-then-password-long-delay")
def check_email(email: str):
    """Validate the submitted e-mail for the long-delay demo."""
    return handle_email_validation(
        email,
        error_form_action="/auth/email-then-password-long-delay",
        error_message="Unknown email",
        success_callback=password_form_callback("/submit/email-then-password/login"),
        delay_seconds=15,
        use_random_delay=False,
    )


@app.post("/submit/email-then-password-long-delay/login")
def check_password(email: str, password: str):
    time.sleep(15)

    if email == VALID_EMAIL and password == VALID_PASSWORD:
        return welcome_page(email)
    return create_password_form(
        email, "Incorrect credentials", action="/submit/email-then-password/login"
    )
