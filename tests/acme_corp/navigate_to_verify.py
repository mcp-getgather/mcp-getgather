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


@app.get("/verify")
def verify_account():
    """Return the verification page after successful login."""
    return Html(
        Head(Title("ACME Corp - Account Verification"), picolink),
        Body(
            Main(
                H1("Account Status"),
                P("Account verified", cls="feedback-message"),
                cls="container",
            )
        ),
    )
