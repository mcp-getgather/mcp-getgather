# ---------------------------------------------------------------------------
# Email -> choose password OR OTP
# ---------------------------------------------------------------------------

import time
import random

from fasthtml.common import (
    Input,
    Label,
    Div,
    Script,
)
from tests.acme_corp.acme_corp import app
from tests.acme_corp.constants import (
    VALID_EMAIL,
    VALID_PASSWORD,
    VALID_OTP,
    MIN_TIME_DELAY,
    MAX_TIME_DELAY,
)
from tests.acme_corp.helpers import render_form, email_fields, welcome_page


def create_verification_choice_form(
    email: str,
    method: str = "password",
    error_message: str | None = None,
):
    radio_fields = [
        Label(
            Input(
                type="radio",
                name="method",
                value="password",
                checked=(method == "password"),
            ),
            " Password",
        ),
        Label(
            Input(
                type="radio",
                name="method",
                value="otp",
                checked=(method == "otp"),
            ),
            " One-time code",
        ),
    ]

    fields = [Input(type="hidden", name="email", value=email), *radio_fields]

    pw_style = "display:block;" if method == "password" else "display:none;"
    otp_style = "display:block;" if method == "otp" else "display:none;"
    fields.append(
        Div(
            Label(
                "Password:",
                Input(
                    type="password",
                    name="password",
                    autofocus=True,
                    required=True,
                ),
            ),
            id="pw-field",
            style=pw_style,
        )
    )
    fields.append(
        Div(
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
            id="otp-field",
            style=otp_style,
        )
    )

    btn_label = "Continue" if method == "password" else "Verify"
    submit_btn = Input(type="submit", value=btn_label, id="submit-btn")
    fields.append(submit_btn)

    js = """
    document.addEventListener('DOMContentLoaded', function() {
      const pw  = document.getElementById('pw-field');
      const otp = document.getElementById('otp-field');
      const btn = document.getElementById('submit-btn');
      const pwInput = pw.querySelector('input[name="password"]');
      const otpInput = otp.querySelector('input[name="otp"]');
      
      function update() {
        const val = document.querySelector('input[name=method]:checked').value;
        if (val==='password') {
          pw.style.display  = 'block';
          otp.style.display = 'none';
          btn.value         = 'Submit';
          pwInput.required  = true;
          otpInput.required = false;
        } else {
          pw.style.display  = 'none';
          otp.style.display = 'block';
          btn.value         = 'Verify';
          pwInput.required  = false;
          otpInput.required = true;
        }
      }
      document.querySelectorAll('input[name=method]')
              .forEach(r=>r.addEventListener('change', update));
      update();
    });
    """
    fields.append(Script(js))

    return render_form(
        fields,
        action="/submit/email-then-password-or-otp/verify",
        error_message=error_message,
    )


@app.get("/auth/email-then-password-or-otp")
def email_only_form_choice():
    """First page: ask for email before choosing verification method."""
    return render_form(
        email_fields,
        action="/auth/email-then-password-or-otp",
    )


@app.post("/auth/email-then-password-or-otp")
def choose_verification_method(email: str):
    """After collecting the email, present the method-selection page."""
    time.sleep(random.uniform(MIN_TIME_DELAY, MAX_TIME_DELAY))

    if email != VALID_EMAIL:
        return render_form(
            email_fields,
            action="/auth/email-then-password-or-otp",
            error_message="Unknown email",
        )

    return create_verification_choice_form(
        email,
        method="password",
    )


@app.post("/submit/email-then-password-or-otp/verify")
def verify_password_or_otp(
    email: str,
    method: str = "password",
    password: str = "",
    otp: str = "",
):
    """Verify credentials based on chosen method and show welcome or error."""
    time.sleep(random.uniform(MIN_TIME_DELAY, MAX_TIME_DELAY))

    success = False
    if method == "password":
        success = email == VALID_EMAIL and password == VALID_PASSWORD
    else:
        success = email == VALID_EMAIL and otp == VALID_OTP

    if success:
        return welcome_page(email)

    error_msg = "Incorrect credentials"
    return create_verification_choice_form(
        email,
        method=method,
        error_message=error_msg,
    )