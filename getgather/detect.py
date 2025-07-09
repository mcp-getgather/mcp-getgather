from getgather.config import settings
from getgather.connectors.spec_models import PageSpec, PageSpecYML


def get_universal_pages() -> list[PageSpec]:
    """Get universal pages that should be available for all brand specs."""
    universal_pages_yml = [
        PageSpecYML(
            name="Chrome Network Error",
            url="chrome-error://chromewebdata/",
            end=True,
            message="❌ Network connection error. Please check your internet connection and try again.",
        ),
    ]

    # Add test-specific universal pages
    if settings.ENVIRONMENT in ["local", "test"]:
        universal_pages_yml.append(
            PageSpecYML(
                name="ACME Test Error Page",
                url="http://localhost:5001/error-page",
                end=True,
                message="❌ Test error page detected. This is a universal test error.",
            )
        )

    return [
        PageSpec.from_yml(page_yml, fields_map={}, pages_map={}) for page_yml in universal_pages_yml
    ]
