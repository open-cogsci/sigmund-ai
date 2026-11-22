"""An MCP (Model Context Protocol) server that exposes Sigmund's documentation
search (RAG) as a single `search_documentation` tool, so that external MCP
clients (AI IDEs, agent frameworks, and so on) can query the Sigmund library.

This module is *not* part of the Flask application. Instead, it is a separate
process that embeds the same ASGI server (uvicorn) via the official `mcp`
SDK, reusing the same configuration, secrets, and documentation library as
the Flask app. Within production, it runs as its own system service that is
a sibling of the gunicorn/flask service.

Configuration (via the environment or .env, see below):
- SIGMUND_MCP_ENABLED: Set to 0 to disable the server. The server refuses to
  start unless this is enabled and a bearer token has been provided.
- SIGMUND_MCP_BEARER_TOKEN: The bearer token that clients must provide. To
  authenticate, MCP clients must send an 'Authorization: Bearer <token>'
  header.
- SIGMUND_MCP_HOST: The host to bind to. Defaults to 127.0.0.1, so that the
  server can be put behind a reverse proxy that deals with TLS and public
  exposure (in production the server should not listen on a public
  interface itself).
- SIGMUND_MCP_PORT: The port at which the server listens. The default is
  8010, just above a commonly used alternative default port of 8000.

The mcp package requires Python 3.10 or later, and is an optional
extra (pip install sigmund[mcp], or pip install "mcp>=2,<3" directly).

Starting the server on a dev machine, from the project root (the path of
the documentation library, config.search_persist_directory, is relative,
just like in the Flask application):
    .venv/bin/python -m sigmund.mcp_server
"""

from __future__ import annotations

try:
    from mcp.server.auth.provider import AccessToken
    from mcp.server.auth.settings import AuthSettings
    from mcp.server.mcpserver import MCPServer
    from mcp.server.mcpserver.exceptions import ToolError
    from mcp.server.transport_security import TransportSecuritySettings
    from mcp_types import ToolAnnotations
    from pydantic import Field
except ImportError as err:
    raise ImportError(
        'The MCP server requires the `mcp` package (version 2 or later). '
        'Install it with: pip install "mcp>=2,<3"') from err

# The environment (.env) needs to be loaded before importing the config,
# because the config reads all environment variables during the import.
# This mirrors what app.py does for the Flask application.
from dotenv import load_dotenv

load_dotenv()

import hashlib
import hmac
import logging
from typing import Annotated
from urllib.parse import urlparse

from . import __version__, config
from .documentation import Documentation
from .library import Library

logger = logging.getLogger('sigmund')


class BearerTokenVerifier:
    """A minimal token verifier that validates tokens by comparing them,
    using constant-time comparison, to the secret in the configuration."""

    def __init__(self, token: str):
        self._token_hash = hashlib.sha256(token.encode()).hexdigest()

    async def verify_token(self, token: str) -> AccessToken | None:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        if hmac.compare_digest(token_hash, self._token_hash):
            return AccessToken(token=token, client_id='sigmund',
                               scopes=[])
        return None


_library = None
"""A single Library is shared for all searches (see _documentation),
because instantiating a library is expensive. The library is only read
from, never written to by the MCP server."""


def _documentation(foundation_document_topics) -> Documentation:
    """Instantiates a Documentation object for a single search.

    The MCP server has no user (and thus no user settings), so all
    collections from the configuration are searched. Because the
    collections are given explicitly, the Documentation object doesn't
    require a sigmund instance with database access, and None can be
    passed instead.
    """
    global _library
    if _library is None:
        logger.info('initializing documentation library')
        _library = Library(
            persist_directory=config.search_persist_directory,
            embedding_provider=config.search_embedding_provider,
            embedding_model=config.search_embedding_model)
    return Documentation(
        None, foundation_document_topics=foundation_document_topics,
        library=_library, collections=config.search_collections)


def create_mcp_server() -> MCPServer:
    """Creates and configures the MCP server with a single
    `search_documentation` tool, using the bearer token from the
    configuration (config.mcp_bearer_token).
    """
    mcp = MCPServer(name='Sigmund documentation search',
                    version=__version__,
                    instructions=(
                        'This server provides a search tool to search the '
                        'Sigmund documentation library by semantic '
                        'similarity, and should be used to look up '
                        'documentation that is relevant to answer user '
                        'questions.'),
                    auth=AuthSettings(
                        issuer_url=config.mcp_issuer,
                        resource_server_url=config.mcp_issuer,
                        required_scopes=[],
                        validate_token_resource=False),
                    token_verifier=BearerTokenVerifier(
                        config.mcp_bearer_token))

    @mcp.tool(
        name='search_documentation',
        title='Search Sigmund documentation',
        annotations=ToolAnnotations(readOnlyHint=True,
                                    destructiveHint=False,
                                    idempotentHint=False,
                                    openWorldHint=False),
        description=(
            'Searches the Sigmund documentation library for documentation '
            'that is relevant to answer a user question. The library is '
            'searched with query-document semantic similarity. The function '
            'returns the relevant documentation, including the URL for each '
            'document, or in case no relevant documentation is found the '
            'function returns an empty result. The optional '
            '`foundation_document_topics` provide foundation topics for '
            'which documentation is always included in the results, even '
            'when that documentation is not related to the query itself.'),
        structured_output=False)
    def search_documentation(
            query: Annotated[str, Field(
                description='The user question to search documentation '
                'for. The query should be a complete, self-contained '
                'question rather than a few keywords, because documents '
                'are found based on semantic similarity.')],
            foundation_document_topics: Annotated[
                list[str] | None, Field(
                    description='Optional foundation topics (such as item '
                    'names) for which foundation documents are always '
                    'included in the result, even when they are not '
                    'themselves semantically similar to the query.')] = None) -> str:
        """Search the Sigmund documentation library (RAG); returns the
        found documents (each with title, source URL and content), or a
        message when no relevant documentation was found.
        """
        if not query or not query.strip():
            raise ToolError('query must be a non-empty string')
        docs = _documentation(foundation_document_topics)
        docs.search(query, howtos=True, foundation=True, fallback=False)
        results = []
        for doc in docs._documents:
            result = {'title': doc.get('title', ''),
                      'url': doc.get('url', ''),
                      'content': doc.get('content', '')}
            results.append(result)
        if not results:
            return ('No relevant documentation was found for this query. '
                    'Try to rephrase the query, or ask a different '
                    'question, or disable documentation search for this '
                    'conversation.')
        out = 'The following documentation was found for this question:\n\n'
        for result in results:
            if result['title']:
                out += f"## {result['title']}\n"
            if result['url']:
                out += f"Source: {result['url']}\n"
            out += result['content'] + '\n\n'
        return out

    return mcp


def _transport_security() -> TransportSecuritySettings:
    """Returns the transport-security settings for the HTTP transport.

    DNS-rebinding protection is enabled, and the allowed hosts are the
    localhost (where the reverse proxy connects, see mcp_host) plus the
    public host of the issuer URL (see mcp_issuer). That way the Host
    header is accepted regardless of whether the reverse proxy keeps the
    original Host header (proxy_set_header Host $host) or sends the
    proxy address (nginx' default behavior).
    """
    issue_parts = urlparse(config.mcp_issuer)
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=['127.0.0.1:*', 'localhost:*', '[::1]:*',
                       issue_parts.netloc],
        allowed_origins=['http://127.0.0.1:*', 'http://localhost:*',
                         'http://[::1]:*',
                         f'{issue_parts.scheme}://{issue_parts.netloc}'])


def mcp_args():
    """Returns the keyword arguments for the MCP server's run function, or
    raises a RuntimeError if the MCP server should not be run.
    """
    if not config.mcp_enabled:
        raise RuntimeError(
            'MCP server not enabled (SIGMUND_MCP_ENABLED is not set)')
    if not config.mcp_bearer_token:
        raise RuntimeError(
            'MCP server requires a bearer token (SIGMUND_MCP_BEARER_TOKEN '
            'is not set)')
    return {'host': config.mcp_host, 'port': config.mcp_port}


def run() -> None:
    """Starts the MCP server. Before doing so, it validates that the server
    should be run; a user-friendly error is raised otherwise.
    """
    logging.basicConfig(level=logging.INFO, force=True)
    args = mcp_args()
    mcp = create_mcp_server()
    # Stateless HTTP mode is used, meaning that each POST request is
    # self-contained and includes the protocol-version header, and no
    # server-side session state is retained between requests. This is the
    # most robust mode to serve simple function calls to external clients.
    logger.info(f"allowing Host headers for: {config.mcp_issuer}")
    mcp.run(transport='streamable-http', streamable_http_path='/mcp',
            json_response=True, stateless_http=True,
            transport_security=_transport_security(), **args)


if __name__ == '__main__':
    run()
