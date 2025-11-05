from tests.acme_corp.acme_corp import app

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
  <head>
    <meta charset=\"utf-8\" />
    <title>A Random Page</title>
  </head>
  <body>
    <main class=\"container\">
      <h1>No Pattern Available</h1>
      <p>This page intentionally lacks any distillation hooks.</p>
    </main>
  </body>
</html>
"""


@app.get("/random-info-page")
def random_info_page():
    return HTML_TEMPLATE
