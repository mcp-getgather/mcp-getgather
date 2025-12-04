from typing import Any

from fasthtml.common import (
    H1,
    H2,
    A,
    Body,
    Div,
    FastHTML,
    Head,
    Html,
    Li,
    Main,
    P,
    Redirect,
    Title,
    Ul,
    picolink,
)

app = FastHTML(hdrs=(picolink,))


@app.get("/")
def index() -> Any:
    return Html(
        Head(Title("ACME Corp"), picolink),
        Body(
            Main(
                H1("ACME Corp"),
                Ul(
                    Li(A("Email and Password", href="/auth/email-and-password")),
                ),
                Ul(
                    Li(A("Email then Password", href="/auth/email-then-password")),
                ),
                Ul(
                    Li(
                        A("Email then Password then MFA", href="/auth/email-then-password-then-mfa")
                    ),
                ),
                Ul(
                    Li(
                        A(
                            "Email and Password in Overlay component",
                            href="/auth/email-password-overlay",
                        )
                    ),
                ),
                Ul(
                    Li(A("Email then OTP", href="/auth/email-then-otp")),
                ),
                Ul(
                    Li(
                        A(
                            "Email then OTP with Multi Inputs",
                            href="/auth/email-then-otp-multi-inputs",
                        )
                    ),
                ),
                Ul(
                    Li(
                        A(
                            "Email and Password with Checkbox",
                            href="/auth/email-and-password-checkbox",
                        )
                    ),
                ),
                Ul(
                    Li(
                        A(
                            "Email then Password with Long Delay",
                            href="/auth/email-then-password-long-delay",
                        )
                    ),
                ),
                Ul(
                    Li(
                        A(
                            "Email and Password Overlay with Hidden Last Name",
                            href="/auth/email-password-lastname-overlay",
                        )
                    ),
                ),
                Ul(
                    Li(
                        A(
                            "Sign-in Error Test (Universal Page)",
                            href="/universal-error-test",
                        )
                    ),
                ),
                Ul(
                    Li(
                        A(
                            "Email then OTP or Password",
                            href="/auth/email-then-otp-or-password",
                        )
                    ),
                ),
                Ul(
                    Li(
                        A(
                            "Email then Password or OTP",
                            href="/auth/email-then-pass-or-otp",
                        )
                    ),
                ),
                Ul(
                    Li(
                        A(
                            "Email then Password or OTP via Radio Buttons",
                            href="/auth/email-then-password-or-otp-radio-buttons",
                        )
                    ),
                ),
                Ul(
                    Li(
                        A(
                            "Email and Password in Iframe",
                            href="/auth/email-password-iframe",
                        ),
                    ),
                ),
                Ul(
                    Li(
                        A(
                            "Email then Password then MFA choice (phone/email)",
                            href="/auth/email-then-password-then-mfa-choice-phone-email",
                        )
                    ),
                ),
                Ul(
                    Li(
                        A(
                            "Email and Password then MFA",
                            href="/auth/email-and-password-then-mfa",
                        )
                    ),
                ),
                Ul(
                    Li(
                        A(
                            "Amazon Orders (Mock)",
                            href="/your-orders/orders?timeFilter=year-2025&startIndex=0&numOrders=200",
                        )
                    ),
                ),
                Ul(
                    Li(
                        A(
                            "Cross-Domain Auth Test",
                            href="/cross-domain",
                        )
                    ),
                ),
                cls="container",
            )
        ),
    )


@app.get("/cross-domain")
def cross_domain():
    """
    Simulates cross-domain authentication flow
    Redirects to auth server (different domain: localhost:5002)
    """
    callback_url = "http://localhost:5001/cross-domain-callback"
    auth_server_url = f"http://localhost:5002/signin?redirect_uri={callback_url}"
    return Redirect(auth_server_url)


@app.get("/cross-domain-callback")
def cross_domain_callback(auth_token: str = "", email: str = "") -> Any:
    """
    Callback endpoint after successful authentication from auth server
    """
    if not auth_token:
        return Html(
            Head(Title("Authentication Failed"), picolink),
            Body(
                Main(
                    H1("Authentication Failed"),
                    P("No auth token received"),
                    A("Try again", href="/cross-domain"),
                    cls="container",
                )
            ),
        )

    return Html(
        Head(Title("ACME Corp - Success"), picolink),
        Body(
            Main(
                H1("Cross-Domain Auth Successful"),
                H2(f"Welcome back, {email}!"),
                P(f"Auth Token: {auth_token}"),
                P("Successfully authenticated via auth server (localhost:5002)"),
                A("Back to home", href="/"),
                cls="container",
            )
        ),
    )
