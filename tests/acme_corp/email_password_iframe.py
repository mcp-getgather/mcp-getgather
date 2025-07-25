# ---------------------------------------------------------------------------
# Email + password + iframe
# ---------------------------------------------------------------------------
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
    Iframe,
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
    VALID_PASSWORD,
)
from tests.acme_corp.helpers import create_email_password_form, welcome_page


def create_login_form(error_message: str = None):
    """Create a login form with email and password fields."""
    return create_email_password_form(
        error_message=error_message,
        action="/submit/email-password-iframe",
    )


@app.get("/auth/iframe-content")
def iframe_content():
    """Render the iframe content with the login form."""
    styles = """
        body {
            margin: 0;
            padding: 20px;
            font-family: system-ui, -apple-system, sans-serif;
        }
        .login-form {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            width: 100%;
            max-width: 320px;
            margin: 0 auto;
        }
        label {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        input {
            padding: 0.5rem;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: 1rem;
        }
        button {
            background: #0066cc;
            color: white;
            border: none;
            padding: 0.75rem;
            border-radius: 4px;
            font-size: 1rem;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        button:hover {
            background: #0052a3;
        }
        .feedback-message {
            color: #dc2626;
            margin: 0.5rem 0;
        }
        .feedback-message.success {
            color: #16a34a;
        }
    """

    return Html(
        Head(Title("Login"), Style(styles), picolink),
        Body(create_login_form()),
    )


@app.get("/auth/email-password-iframe")
def main_page():
    """Render the main page with a button that triggers the login iframe."""
    styles = """
        .iframe-container {
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
        .iframe-wrapper {
            background: white;
            padding: 0;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            width: 400px;
            height: 350px;
            overflow: hidden;
        }
        .iframe-container.active {
            display: flex;
        }
        iframe {
            width: 100%;
            height: 100%;
            border: none;
        }
    """

    script = """
        function toggleIframe() {
            document.getElementById('loginIframe').classList.toggle('active');
        }
        
        // Close iframe when clicking outside
        document.addEventListener('click', function(event) {
            const container = document.getElementById('loginIframe');
            const wrapper = document.querySelector('.iframe-wrapper');
            if (container.classList.contains('active') && 
                event.target === container) {
                container.classList.remove('active');
            }
        });
        
        // Close iframe when pressing Escape
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                document.getElementById('loginIframe').classList.remove('active');
            }
        });
    """

    return Html(
        Head(Title("ACME Corp - Iframe Login"), Style(styles), picolink),
        Body(
            Main(
                H1("Welcome to ACME Corp"),
                Button("Sign in", onclick="toggleIframe()"),
                Div(
                    Div(
                        Iframe(src="/auth/iframe-content"),
                        cls="iframe-wrapper",
                    ),
                    id="loginIframe",
                    cls="iframe-container",
                ),
                cls="container",
            ),
            Script(script),
        ),
    )


@app.post("/submit/email-password-iframe")
def handle_login(email: str, password: str):
    """Handle the login form submission."""
    time.sleep(random.uniform(MIN_TIME_DELAY, MAX_TIME_DELAY))

    if email == VALID_EMAIL and password == VALID_PASSWORD:
        return Html(
            Head(Title("Login Successful"), picolink),
            Body(
                Script("""
                    // Replace the parent window's content with the welcome page
                    window.parent.location.href = '/auth/success';
                """),
            ),
        )

    return iframe_content()


@app.get("/auth/success")
def success():
    """Render the success page after login."""
    return welcome_page(VALID_EMAIL)
