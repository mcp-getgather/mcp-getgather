import time

from fasthtml.common import (
    Button,
    Form,
    Head,
    Html,
    Input,
    P,
    Script,
    Title,
    picolink,
)
from fasthtml.core import JSONResponse

from tests.acme_corp.acme_corp import app


@app.get("/submit_form")
def submit_form():
    return Html(
        Head(Title("ACME Corp"), picolink),
        Form(
            Input(type="text", name="message", value="Hello, world!", required=True),
            Input(type="hidden", name="response_type", value="html", required=True),
            Button("Submit", type="submit"),
            action="/submit_handler",
            enctype="application/x-www-form-urlencoded",
            method="post",
        ),
        cls="container",
    )


@app.post("/submit_handler")
def submit_handler(message: str, response_type: str):
    time.sleep(20)
    if response_type == "html":
        return Html(P(f"Message received: {message}"))
    elif response_type == "json":
        return JSONResponse({"message": message})
    else:
        return JSONResponse({"error": "Invalid response_type"}, status_code=400)


@app.get("/submit_js_inline")
def submit_js_inline():
    return _submit_js("inline")


@app.get("/submit_js_route")
def submit_js_route():
    return _submit_js("route")


def _submit_js(update_type: str):
    if update_type == "inline":
        update_script = """
            const result = await response.json();
            document.getElementById('message').innerHTML = "Message received: " + result.message;
        """
    elif update_type == "route":
        update_script = """
            const result = await response.json();
            if (response.ok) {
                window.location.href = '/submit_success?message=' + result.message;
            }
        """
    else:
        return JSONResponse({"error": "Invalid update_type"}, status_code=400)

    script = f"""
    document.addEventListener('DOMContentLoaded', function() {{
        const form = document.querySelector('form');
        form.addEventListener('submit', async function(e) {{
            e.preventDefault();
            document.querySelector('button[type="submit"]').style.display = 'none';
            
            const formData = new FormData(form);
            const response = await fetch('/submit_handler', {{
                method: 'POST',
                body: formData
            }});

            {update_script}
        }});
    }});
    """

    return Html(
        Head(Title("ACME Corp"), picolink),
        Form(
            Input(type="text", name="message", value="Hello, world!", required=True),
            Input(type="hidden", name="response_type", value="json", required=True),
            Button("Submit", type="submit"),
        ),
        P(id="message"),
        Script(script),
        cls="container",
    )


@app.get("/submit_success")
def submit_success(message: str):
    return Html(P(f"Message received: {message}"))
