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

from tests.acme_corp.constants import VALID_EMAIL


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