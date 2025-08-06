# --------------------------------------------------------------
# Shared helpers / constants
# --------------------------------------------------------------

import random
import time
from typing import Callable, Union

from fasthtml.common import (
    H1,
    A,
    Body,
    Button,
    Div,
    Form,
    Head,
    Html,
    Input,
    Label,
    Main,
    P,
    Script,
    Title,
    picolink,
)

from tests.acme_corp.constants import MAX_TIME_DELAY, MIN_TIME_DELAY, VALID_EMAIL, VALID_OTP


def create_email_password_form(
    error_message: str | None = None,
    *,
    show_remember_me: bool = False,
    action: str = "/submit/email-and-password",
    email_validation: bool = False,
):
    """One-page email + password login using the shared render_form.

    Args:
        error_message: Optional error message to display
        show_remember_me: Whether to show the "Remember me" checkbox
    """
    fields = [
        Label("Email:", Input(type="email", name="email", required=True)),
        Label("Password:", Input(type="password", name="password", required=True)),
        Button("Log in", type="submit"),
    ]

    email_script = f"""
        document.addEventListener('DOMContentLoaded', function() {{
            const passwordInput = document.querySelector('input[name="password"]');
            const submitButton = document.querySelector('button[type="submit"]');
            passwordInput.style.display = 'none';
            submitButton.disabled = true;

            const emailInput = document.querySelector('input[name="email"]');
            emailInput.addEventListener('keyup', function(e) {{
                const isEmailValid = this.value === '{VALID_EMAIL}';
                passwordInput.style.display = isEmailValid ? 'block' : 'none';
                submitButton.disabled = !isEmailValid;
            }});
        }});
    """

    if show_remember_me:
        fields.append(Label("Remember me", Input(type="checkbox", name="remember_me")))

    return render_form(
        fields,
        action=action,
        error_message=error_message,
        script=email_script if email_validation else None,
    )


def render_form(
    fields: list,
    action: str,
    title: str = "Login",
    error_message: str | None = None,
    script: str | None = None,
):
    """Return a complete <html> page for ACME forms."""
    if error_message:
        fields.append(Div(P(f"❌ {error_message}"), cls="feedback-message"))

    # Standard page shell.
    return Html(
        Head(Title("ACME Corp"), picolink),
        Body(
            Main(
                H1(title),
                Form(
                    *fields,
                    action=action,
                    enctype="application/x-www-form-urlencoded",
                    method="post",
                ),
                cls="container",
            ),
            Script(script) if script else None,
        ),
    )


def welcome_page(email: str):
    """Return the success page after a completed login."""
    return Html(
        Head(Title("Welcome to ACME Corp"), picolink),
        Body(
            Main(
                H1("Login successful!"),
                P(f"Welcome, {email}.", cls="feedback-message"),
                P(A("Home Page", href="/"), cls="home-link"),
                cls="container",
            )
        ),
    )


email_fields: list[Union[Label, Input, Button]] = [  # noqa
    Label(
        "Email:",
        Input(
            type="email",
            name="email",
            autofocus=True,
            autocomplete="email",
            required=True,
        ),
    ),
    Button("Continue", type="submit"),
]


def create_email_form(
    error_message: str | None = None, action: str = "/submit/email-then-password/next"
):
    """First page in the two-step flow (email → password)."""
    return render_form(email_fields, action=action, error_message=error_message)


def create_otp_form(
    email: str, action: str, *, error_message: str | None = None, multi_inputs: bool = False
):
    """Second page in the two-step flow (password entry)."""
    if multi_inputs:
        otp_input = Label(
            "One-time code:",
            Div(
                *[
                    Input(
                        type="text",
                        name=f"otp_{i + 1}",
                        maxlength=1,
                        required=False,
                    )
                    for i in range(len(VALID_OTP))
                ],
                cls="grid",
            ),
            Input(type="text", name="otp", hidden=True),
        )
    else:
        otp_input = Label(
            "One-time code:",
            Input(type="text", name="otp", autofocus=True, required=True),
        )

    fields = [
        Input(type="email", name="email", hidden=True, required=True, value=email),
        otp_input,
        Button("Log in", type="submit"),
    ]
    script = """
        document.addEventListener('DOMContentLoaded', function() {
            const form = document.querySelector('form');
            const otpDigitInputs = document.querySelectorAll('input[name^="otp_"]');
            
            // Auto-focus and navigation logic
            otpDigitInputs.forEach((input, index) => {
                if (index === 0) input.focus();
                
                input.addEventListener('input', function(e) {
                    // Only allow numbers
                    this.value = this.value.replace(/[^0-9]/g, '');
                    
                    // Auto-advance to next input
                    if (this.value.length === 1 && index < otpDigitInputs.length - 1) {
                        otpDigitInputs[index + 1].focus();
                    }
                });
                
                input.addEventListener('keydown', function(e) {
                    // Handle backspace navigation
                    if (e.key === 'Backspace' && this.value === '' && index > 0) {
                        otpDigitInputs[index - 1].focus();
                    }
                });
            });
            
            // Merge OTP inputs before form submission
            form.addEventListener('submit', function(e) {
                let otpInput = form.querySelector('input[name="otp"]');
                if (otpDigitInputs.length > 0) {  // multi-inputs case
                    const otpValues = Array.from(otpDigitInputs).map(input => input.value).join('');
                    otpInput.value = otpValues;
                    
                    // Remove individual OTP inputs from form submission
                    otpDigitInputs.forEach(input => input.disabled = true);
                } // single-input case
            });
        });
    """
    return render_form(
        fields,
        action=action,
        error_message=error_message,
        script=script,
    )


def create_password_form(
    email: str, error_message: str | None = None, action: str = "/submit/email-then-password/login"
):
    """Second page in the two-step flow (password entry)."""
    fields = [
        Input(
            type="email",
            name="email",
            hidden=True,
            required=True,
            value=email,
        ),
        Label(
            "Password:",
            Input(
                type="password",
                name="password",
                autofocus=True,
                required=True,
            ),
        ),
        Button("Log in", type="submit"),
    ]
    return render_form(
        fields,
        action=action,
        error_message=error_message,
    )


def handle_email_validation(
    email: str,
    *,
    error_form_action: str,
    error_message: str = "Invalid email address",
    success_callback: Callable[[str], any],
    delay_seconds: float | None = None,
    use_random_delay: bool = True,
):
    """
    Handle common email validation pattern across different routes.

    Args:
        email: The email to validate
        error_form_action: The action URL for the error form
        error_message: Custom error message for invalid email
        success_callback: Function to call on successful validation (receives email)
        delay_seconds: Fixed delay in seconds (overrides random delay)
        use_random_delay: Whether to use random delay (ignored if delay_seconds is set)

    Returns:
        Either error form or result from success_callback
    """
    # Handle delay
    if delay_seconds is not None:
        time.sleep(delay_seconds)
    elif use_random_delay:
        time.sleep(random.uniform(MIN_TIME_DELAY, MAX_TIME_DELAY))

    # Validate email
    if email != VALID_EMAIL:
        return create_email_form(
            action=error_form_action,
            error_message=error_message,
        )

    # Call success callback with the validated email
    return success_callback(email)


# Common success callback factories for typical patterns
def password_form_callback(action: str):
    """Factory function for creating password form callbacks."""

    def callback(email: str):
        return create_password_form(email, action=action)

    return callback


def signin_page(action: str = "/error-page"):
    """Simple sign-in page that navigates to error page when submitted."""
    return Html(
        Head(Title("ACME Corp - Sign In Test"), picolink),
        Body(
            Main(
                H1("🏢 ACME Corp Sign In"),
                P("Click 'Sign In' to continue"),
                Form(
                    Button(
                        "Sign In",
                        type="submit",
                        style="width: auto; padding: 0.5rem 1rem;",
                        **{"data-testid": "signin-button"},
                    ),
                    action=action,
                    method="post",
                ),
                cls="container",
            )
        ),
    )
