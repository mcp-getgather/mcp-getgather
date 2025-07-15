import random
import time

from fasthtml.common import (
    H1,
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
    Style,
    Title,
    picolink,
)

from tests.acme_corp.acme_corp import app
from tests.acme_corp.constants import (
    MAX_TIME_DELAY,
    MIN_TIME_DELAY,
    VALID_EMAIL,
    VALID_LASTNAME,
    VALID_PASSWORD,
)
from tests.acme_corp.helpers import welcome_page


def create_overlay_form(error_message: str = None):
    """Create an overlay form with email, last name, and password fields."""
    form_fields = [
        Label("Email:", Input(type="email", name="email", id="email", required=True)),
        Div(
            Label("Last Name:", Input(type="text", name="lastname", required=True)),
            id="lastnameField",
            style="display: none;",
        ),
        Label("Password:", Input(type="password", name="password", required=True)),
        Button("Sign in", type="submit"),
    ]

    if error_message:
        form_fields.append(Div(P(f"❌ {error_message}"), cls="feedback-message"))

    return Div(
        Form(
            *form_fields,
            action="/submit/email-password-lastname-overlay",
            method="post",
            cls="overlay-form",
        ),
        id="loginOverlay",
        cls="overlay",
    )


@app.get("/auth/email-password-lastname-overlay")
def overlay_login_page():
    """Render the main page with a button that triggers the login overlay."""
    styles = """
        .overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            justify-content: center;
            align-items: center;
        }
        .overlay-form {
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        .overlay.active {
            display: flex;
        }
        #lastnameField {
            transition: opacity 0.3s ease;
        }
    """

    script = """
        function toggleOverlay() {
            document.getElementById('loginOverlay').classList.toggle('active');
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            const emailInput = document.getElementById('email');
            const lastnameField = document.getElementById('lastnameField');
            
            emailInput.addEventListener('input', function() {
                if (this.value.trim() !== '') {
                    lastnameField.style.display = 'block';
                } else {
                    lastnameField.style.display = 'none';
                }
            });
        });
    """

    return Html(
        Head(Title("ACME Corp - Overlay Login"), Style(styles), picolink),
        Body(
            Main(
                H1("Welcome to ACME Corp"),
                Button("Sign in", onclick="toggleOverlay()"),
                create_overlay_form(),
                cls="container",
            ),
            Script(script),
        ),
    )


@app.post("/submit/email-password-lastname-overlay")
def overlay_login_submit(email: str, lastname: str, password: str):
    """Handle the login form submission."""
    time.sleep(random.uniform(MIN_TIME_DELAY, MAX_TIME_DELAY))

    if email == VALID_EMAIL and password == VALID_PASSWORD and lastname == VALID_LASTNAME:
        return welcome_page(email)

    return overlay_login_page()
