from typing import Any
from fasthtml.common import (
    H1,
    A,
    Body,
    FastHTML,
    Head,
    Html,
    Li,
    Main,
    Title,
    Ul,
    picolink,
)

app = FastHTML(hdrs=(picolink,))


@app.get("/")  # type: ignore
def index() -> Any:
    return Html(
        Head(Title("ACME Corp"), picolink),
        Body(
            Main(
                H1("ACME Corp"),
                Ul(
                    Li(
                        A(
                            "Email and Password with Checkbox",
                            href="/auth/email-and-password-checkbox",
                        )
                    ),
                ),
                cls="container",
            )
        ),
    )
