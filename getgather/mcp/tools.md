# MCP Tools

## A sample list of MCP tools available through the unified GetGather MCP Server

This list is non-exhaustive and only includes a sampling of the full set of MCP tools available on the server.

## Brand Specific Tools

Each brand added to the unified MCP runns as its own **individual FastMCP server instance**. Each brand has its own server instance defined in the spec file under the `/mcp/brand/` directory. For example, in `goodreads.py` the Goodreads MCP is initialized as such:

`goodreads_mcp = FastMCP[Any](name="Goodreads MCP")`

When each individual server is mounted to the main one, a `prefix` argument is added.

`mcp.mount(server=goodreads_mcp, prefix="goodreads")`

This prefix argument makes it so that the tools in that server become accessible as `goodreads_{{tool name}}` (or whatever the prefix is defined as, depending on the brand).

### Why this pattern?

1. **Modular organization**: Each brand's functionality is in its own MCP server
2. **Avoid naming conflicts**: Multiple brands might have similar tool names like get_orders
3. **Clear namespacing**: You know which brand a tool belongs to by its prefix
4. **Authentication context**: The middleware can extract the brand from the tool name by splitting the tool call.

### Authentication Note

Tools that require authentication will trigger the authentication process automatically through the MCP client if the user is not already authenticated for that brand.

Here is a list of current brand specific tools:

### `goodreads_get_book_list`

Tool for retrieving all the books on a user's booklist, not limited to any amount of time. Requires authentication.

### `bbc_get_bookmarks`

Tool for retrieving all bookmarks saved on BBC. Requires authentication.

### `ebird_get_life_list`

Tool for retrieving a user's complete life list from eBird - all bird species they have observed and recorded. Requires authentication.

### `ebird_get_explore_species_list`

Tool for searching and getting a list of bird species from eBird's explore feature by keyword. Returns species names and scientific names. No authentication required.

### `ebird_explore_species`

Tool for exploring detailed information about a specific bird species on eBird using its scientific name. Returns species description, identification details, and statistics. Scientific name of the species is required as a parameter. No authentication required.

## General Tools

These tools are available on the main MCP server (not brand-specific):

### `poll_signin`

Tool for polling the sign in status of a hosted link session. Used to check if a user has completed the login process for a brand. Takes a session ID as input and returns the current sign in status.
