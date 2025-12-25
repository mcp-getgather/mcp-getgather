"""
ACME Corp Browser Error Pages

Test endpoints that mimic Chrome browser error pages for testing
error pattern detection with both Playwright and zendriver.
"""

from fasthtml.common import (
    Body,
    Div,
    Head,
    Html,
    P,
    Title,
)

from tests.acme_corp.acme_corp import app


def chrome_error_page(title: str, error_code: str, message: str):
    """Generate an HTML page that mimics Chrome's error page structure."""
    return Html(
        Head(Title(title)),
        Body(
            Div(
                Div(P(message), id="main-message"),
                Div(error_code, cls="error-code"),
            ),
        ),
    )


@app.get("/error/timed-out")
def error_timed_out():
    """Mimics Chrome's ERR_TIMED_OUT error page."""
    return chrome_error_page(
        title="Error: Timed Out",
        error_code="ERR_TIMED_OUT",
        message="This site took too long to respond.",
    )


@app.get("/error/ssl-protocol-error")
def error_ssl_protocol():
    """Mimics Chrome's ERR_SSL_PROTOCOL_ERROR page."""
    return chrome_error_page(
        title="Error: SSL Protocol Error",
        error_code="ERR_SSL_PROTOCOL_ERROR",
        message="This site sent an invalid response.",
    )


@app.get("/error/tunnel-connection-failed")
def error_tunnel_connection():
    """Mimics Chrome's ERR_TUNNEL_CONNECTION_FAILED page."""
    return chrome_error_page(
        title="Error: Tunnel Connection Failed",
        error_code="ERR_TUNNEL_CONNECTION_FAILED",
        message="This site might be temporarily down or it may have moved permanently to a new web address.",
    )


@app.get("/error/proxy-connection-failed")
def error_proxy_connection():
    """Mimics Chrome's ERR_PROXY_CONNECTION_FAILED page."""
    return chrome_error_page(
        title="Error: Proxy Connection Failed",
        error_code="ERR_PROXY_CONNECTION_FAILED",
        message="There is something wrong with the proxy server.",
    )
