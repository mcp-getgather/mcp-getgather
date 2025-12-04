"""
Auth Server - Simulates external SSO provider (separate domain)
Runs on port 5002 to simulate cross-domain authentication
"""

from typing import Any

from fasthtml.common import (
    H1,
    H2,
    A,
    Body,
    Button,
    Div,
    FastHTML,
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

app = FastHTML(hdrs=(picolink,))


@app.get("/signin")
def signin(redirect_uri: str = "") -> Any:
    """
    SSO signin page - simulates external authentication provider
    Expects redirect_uri parameter to return to ACME Corp
    """
    return Html(
        Head(Title("Auth Server - Sign In"), picolink),
        Body(
            Main(
                H1("Auth Server"),
                H2("Sign in to continue"),
                P("This simulates external SSO provider (separate domain: localhost:5002)"),
                Form(
                    Div(
                        Label("Email", _for="email"),
                        Input(
                            type="email",
                            id="email",
                            name="email",
                            placeholder="you@example.com",
                            required=True,
                        ),
                    ),
                    Div(
                        Label("Password", _for="password"),
                        Input(
                            type="password",
                            id="password",
                            name="password",
                            placeholder="Enter your password",
                            required=True,
                        ),
                    ),
                    Input(type="hidden", name="redirect_uri", value=redirect_uri),
                    Button("Sign In", type="submit"),
                    method="post",
                    action="/signin/submit",
                ),
                cls="container",
            )
        ),
    )


@app.post("/signin/submit")
def signin_submit(email: str, password: str, redirect_uri: str = "") -> Any:
    """
    Process signin and redirect back to ACME Corp
    """
    # In real scenario, would validate credentials
    # For testing, we just redirect back with a token
    if not redirect_uri:
        redirect_uri = "http://localhost:5001/auth/callback"

    # Add auth token to redirect URL
    callback_url = f"{redirect_uri}?auth_token=mock_token_12345&email={email}"

    return Html(
        Head(
            Title("Redirecting..."),
            picolink,
        ),
        Body(
            Main(
                H1("Authentication Successful"),
                P(f"Redirecting back to ACME Corp..."),
                P(A("Click here if not redirected", href=callback_url)),
                cls="container",
            ),
            # Auto-redirect using meta refresh
            Head(Html(f'<meta http-equiv="refresh" content="1;url={callback_url}" />')),
        ),
    )
