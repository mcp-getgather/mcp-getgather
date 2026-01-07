"""HTML template renderer for dpage forms."""

DEFAULT_TITLE = "Sign In"


def render_form(content: str, title: str = DEFAULT_TITLE, action: str = "") -> str:
    """Render HTML form with the given content and options."""
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
    <style>
      :root {{
        --primary: #0a0a0a;
        --primary-dark: #090909;
        --gray-50: #f9fafb;
        --gray-200: #e5e7eb;
        --gray-300: #d1d5db;
        --gray-600: #4b5563;
        --gray-800: #1f2937;
        --gray-900: #111827;
      }}

      * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
      }}

      body {{
        font-family: "Inter", system-ui, -apple-system, sans-serif;
        background-color: var(--gray-50);
        min-height: 100vh;
        display: grid;
        place-items: center;
        padding: 1rem;
        line-height: 1.6;
      }}

      .card {{
        background: white;
        border-radius: 16px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        border: 1px solid var(--gray-200);
        padding: 2rem;
        width: 100%;
        max-width: 480px;
      }}

      .header {{
        text-align: center;
      }}

      .logo {{
        width: 48px;
        height: 48px;
        background: var(--primary);
        border-radius: 12px;
        margin: 0 auto 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 1.25rem;
      }}

      h1, h2 {{
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--gray-900);
        margin-bottom: 0.5rem;
      }}

      .subtitle {{
        color: var(--gray-600);
        font-size: 0.875rem;
        margin-bottom: 1rem;
      }}

      form {{
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
      }}

      label {{
        display: block;
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--gray-800);
      }}
      
      .radio-wrapper {{
        display: flex;
        align-items: center;
        gap: 10px;
      }}
      
      .vertical-radios {{
        gap: 1rem; 
        display: flex; 
        flex-direction: column; 
        margin-bottom: 1rem; 
        margin-top: 1rem;
      }}

      input[type="email"],
      input[type="password"],
      input[type="text"],
      input[type="tel"],
      input[type="url"],
      input[type="number"],
      select,
      textarea {{
        width: 100%;
        padding: 0.75rem 1rem;
        border: 1px solid var(--gray-300);
        border-radius: 8px;
        font-size: 1rem;
        transition: all 0.15s ease;
        background: white;
      }}

      input:focus,
      select:focus,
      textarea:focus {{
        outline: none;
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.1);
      }}

      input[type="checkbox"] {{
        width: 1rem;
        height: 1rem;
        accent-color: var(--primary);
        border-radius: 4px;
      }}

      button[type="submit"],
      button,
      input[type="submit"] {{
        width: 100%;
        background: var(--primary);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.875rem 1rem;
        font-size: 1rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.15s ease;
      }}

      button[type="submit"]:hover,
      button:hover,
      input[type="submit"]:hover {{
        background: var(--primary-dark);
      }}

      button[type="submit"]:focus,
      button:focus,
      input[type="submit"]:focus {{
        outline: none;
        box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.2);
      }}

      .content-wrapper {{
        display: flex;
        flex-direction: column;
        gap: 1rem;
      }}
      
    .content-wrapper
      :is(a, div, p, span, h1, h2, h3, h4, h5, h6):empty {{
      display: none;
    }}

      @media (max-width: 640px) {{
        .card {{
          padding: 1.5rem;
          max-width: 100%;
        }}
      }}
      
      /* Loading spinner styles */
      .spinner {{
        display: inline-block;
        width: 16px;
        height: 16px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-top-color: white;
        border-radius: 50%;
        animation: spin 0.6s linear infinite;
        margin-right: 8px;
        vertical-align: middle;
      }}

      @keyframes spin {{
        to {{ transform: rotate(360deg); }}
      }}

      button:disabled,
      input[type="submit"]:disabled {{
        opacity: 0.7;
        cursor: not-allowed;
      }}

      .form-overlay {{
        position: absolute;
        inset: 0;
        background: rgba(255, 255, 255, 0.6);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10;
        border-radius: inherit;
      }}

      form {{
        position: relative;
      }}

      /* Shared OTP/PIN input container styles */
      .otp-container,
      .pin-container {{
        display: flex;
        gap: 10px;
        justify-content: center;
      }}

      .otp-container input,
      .pin-container input {{
        flex: 0 0 50px;
        width: 50px;
        height: 50px;
        font-size: 24px;
        text-align: center;
        border: 2px solid var(--gray-300);
        border-radius: 8px;
        outline: none;
        transition: border-color 0.2s ease;
        padding: 0;
      }}

      .otp-container input:focus,
      .pin-container input:focus {{
        border-color: var(--primary);
      }}
    </style>
    <script>
      document.addEventListener("DOMContentLoaded", function () {{
        const form = document.querySelector("div.card");

        if (form) {{
          form.addEventListener("submit", function (e) {{

            const overlay = document.createElement("div");
            overlay.className = "form-overlay";

            const spinner = document.createElement("div");
            spinner.className = "spinner";
            spinner.style.borderTopColor = "#333";

            overlay.appendChild(spinner);
            form.appendChild(overlay);
          }});
        }}

        // Auto-focus for OTP/PIN containers
        const otpContainers = document.querySelectorAll(".otp-container, .pin-container");
        otpContainers.forEach(function(container) {{
          const inputs = container.querySelectorAll("input");
          inputs.forEach(function(input, index) {{
            input.addEventListener("input", function(e) {{
              if (e.target.value && index < inputs.length - 1) {{
                inputs[index + 1].focus();
              }}
            }});
            input.addEventListener("keydown", function(e) {{
              if (e.key === "Backspace" && !input.value && index > 0) {{
                inputs[index - 1].focus();
              }}
            }});
            input.addEventListener("paste", function(e) {{
              e.preventDefault();
              const pastedData = e.clipboardData.getData("text").trim();
              const digits = pastedData.replace(/\D/g, "").split("");
              digits.forEach(function(digit, i) {{
                if (index + i < inputs.length) {{
                  inputs[index + i].value = digit;
                }}
              }});
              if (digits.length > 0) {{
                const lastFilledIndex = Math.min(index + digits.length - 1, inputs.length - 1);
                if (inputs[lastFilledIndex]) {{
                  inputs[lastFilledIndex].focus();
                }}
              }}
            }});
          }});
        }});
      }});
    </script>
  </head>
  <body>
    <div class="card">
      <div class="header">
        <h2>{title}</h2>
      </div>
      <form method="POST" action="{action}">
        <div class="content-wrapper">
          {content}
        </div>
      </form>
    </div>
  </body>
</html>"""
