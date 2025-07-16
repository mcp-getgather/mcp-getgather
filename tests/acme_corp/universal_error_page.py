"""
ACME Corp Sign-in Error Page Extension

Simple test endpoints for testing universal error page detection.
Uses fasthtml like other ACME test files.
"""

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
    Title,
    picolink,
)

from tests.acme_corp.acme_corp import app
from tests.acme_corp.helpers import signin_page


@app.get("/universal-error-test")
def signin_error_page():
    return signin_page("/error-page")


@app.post("/error-page")
def error_page(username: str = "", password: str = ""):
    """Error page that should be detected as a universal error page."""
    return Html(
        Head(Title("ACME Corp - Error"), picolink),
        Body(
            Main(
                Div(
                    H1("⚠️ Authentication Error"),
                    P("This is a test error page for universal error detection."),
                    Div(
                        P(f"Error Code: ACME_AUTH_ERROR_001"),
                        style="background: #f8f9fa; padding: 1rem; border-radius: 4px; margin: 1rem 0;",
                    ),
                ),
                cls="container",
            )
        ),
    )
