from typing import cast

from fastapi import FastAPI
from fastmcp.server.auth.providers.github import GitHubProvider
from mcp.server.auth.middleware.auth_context import AuthContextMiddleware
from mcp.server.auth.middleware.bearer_auth import (
    BearerAuthBackend,
    RequireAuthMiddleware,
)
from mcp.server.auth.provider import TokenVerifier
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.types import Receive, Scope, Send

from getgather.config import settings

ALLOWED_CLIENT_REDIRECT_URIS = [
    # For Claude Desktop: see https://support.anthropic.com/en/articles/11503834-building-custom-connectors-via-remote-mcp-servers
    "https://claude.ai/api/mcp/auth_callback",
    "https://claude.com/api/mcp/auth_callback",
    "cursor://anysphere.cursor-retrieval/oauth/user-getgather-books/callback",  # For Cursor
    "http://localhost:*",  # For local development
]


class RequireAuthMiddlewareCustom(RequireAuthMiddleware):
    """Custom RequireAuthMiddleware to require authentication for MCP routes"""

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        path = scope.get("path")
        if path and path.startswith("/mcp"):
            await super().__call__(scope, receive, send)
        else:
            await self.app(scope, receive, send)


def setup_mcp_auth(app: FastAPI, mcp_routes: list[str]):
    github_auth_provider = GitHubProvider(
        client_id=settings.OAUTH_GITHUB_CLIENT_ID,
        client_secret=settings.OAUTH_GITHUB_CLIENT_SECRET,
        base_url=settings.SERVER_ORIGIN,
        redirect_path=settings.OAUTH_GITHUB_REDIRECT_PATH,
        required_scopes=["user"],
        allowed_client_redirect_uris=ALLOWED_CLIENT_REDIRECT_URIS,
    )

    # Set up OAuth routes
    for route in github_auth_provider.get_routes():
        app.add_route(
            route.path,
            route.endpoint,
            list(route.methods) if route.methods else [],
        )

        # handle '/.well-known/oauth-authorization-server/mcp-*' and
        # '/.well-known/oauth-authorization-server/mcp-*'
        if route.path.startswith("/.well-known"):
            for mcp_route in mcp_routes:
                app.add_route(
                    f"{route.path}{mcp_route}",
                    route.endpoint,
                    list(route.methods) if route.methods else [],
                )

    # Set up OAuth middlewares
    auth_middleware = [
        Middleware(
            RequireAuthMiddlewareCustom,
            getattr(github_auth_provider, "required_scopes", None) or [],
            github_auth_provider.get_resource_metadata_url(),
        ),
        Middleware(
            AuthenticationMiddleware,
            backend=BearerAuthBackend(cast(TokenVerifier, github_auth_provider)),
        ),
        Middleware(AuthContextMiddleware),
    ]

    for middleware in auth_middleware:
        app.add_middleware(middleware.cls, *middleware.args, **middleware.kwargs)
