"""Tests for the MCP server (sigmund/mcp_server.py).

The tests exercise the MCP server through its actual Starlette app (via
starlette's TestClient), so that the JSON-RPC layer and the bearer-token
authentication are tested the way an external MCP client would
experience them.

The tests use the classic MCP protocol revision with the initialize
handshake (2025-06-18, the latest revision in
mcp.types.HANDSHAKE_PROTOCOL_VERSIONS), because that is what current
mainstream MCP clients speak. (Newer draft revisions use a per-request
envelope instead of a handshake.)

The tests that perform actual searches require the locally indexed
documentation library (see config.search_persist_directory) and perform
real query embeddings through the OpenAI API (OPENAI_API_KEY). They are
skipped when either is missing, which is the case on CI.
"""
import os.path
import unittest
from unittest import mock

try:
    # The environment must be loaded before the config is imported,
    # because the config reads (and caches) all environment variables
    # during the import. This mirrors what app.py and
    # sigmund/mcp_server.py do.
    from dotenv import load_dotenv

    load_dotenv()

    from starlette.testclient import TestClient

    from sigmund import config, mcp_server
except ImportError:
    # The mcp package is an optional dependency (see the mcp extras in
    # pyproject.toml). Without it none of these tests can run, so the
    # entire module is skipped. Raising unittest.SkipTest at the module
    # level marks the module as skipped, which is handled both by
    # unittest and by pytest.
    raise unittest.SkipTest('this test module requires the mcp package')

# A realistic search query for OpenSesame documentation. Because the
# search is based on semantic similarity, the query should be a full
# self-contained question, not just keywords.
SEARCH_QUERY = ('How do I use a keyboard_response item in OpenSesame to '
                'collect a response, and how do I log the response?')
TOKEN = 'unittest-bearer-token'
PROTOCOL_VERSION = '2025-06-18'

# Whether the search tests can run (see the module docstring).
LIBRARY_EXISTS = os.path.exists(
    os.path.join(config.search_persist_directory, 'chroma.sqlite3'))
HAS_API_KEY = bool(os.environ.get('OPENAI_API_KEY')
                   or config.openai_api_key)


def _headers(extra=None):
    """The headers that a conforming MCP client sends with each request."""
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'MCP-Protocol-Version': PROTOCOL_VERSION,
        'Accept': 'application/json, text/event-stream',
        'Content-Type': 'application/json',
    }
    if extra:
        headers.update(extra)
    return headers


class McpServerTestCase(unittest.TestCase):
    """Base class that provides a client for the MCP server app with a
    known bearer token.
    """

    def setUp(self):
        super().setUp()
        # The module-global library is reset, so that it is initialized
        # anew by each test (with the settings of that test).
        mcp_server._library = None
        self.addCleanup(setattr, mcp_server, '_library', None)
        patcher = mock.patch.object(config, 'mcp_bearer_token', TOKEN)
        patcher.start()
        self.addCleanup(patcher.stop)
        server = mcp_server.create_mcp_server()
        self.app = server.streamable_http_app(stateless_http=True,
                                              json_response=True)
        # The TestClient is entered as a context manager (rather than
        # only instantiated), because only then does starlette run the
        # lifespan (startup and shutdown) handlers of the ASGI app,
        # which the transport requires to initialize its task group. The
        # base URL is the local address of the server, so that the Host
        # header is accepted by the transport's DNS-rebinding protection.
        client_cm = TestClient(
            self.app,
            base_url=f'http://127.0.0.1:{config.mcp_port}')
        self.client = client_cm.__enter__()
        self.addCleanup(client_cm.__exit__, None, None, None)

    def initialize(self):
        """Performs the initialize handshake, as any MCP client must do
        before calling tools, and returns the server info.
        """
        response = self.client.post('/mcp', json={
            'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
            'params': {
                'protocolVersion': PROTOCOL_VERSION,
                'capabilities': {},
                'clientInfo': {'name': 'unittest', 'version': '1.0'},
            }
        }, headers=_headers())
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()['result']
        # Conforming clients confirm the handshake with a notification,
        # to which the server (in stateless json-response mode) replies
        # with 202 Accepted (no body).
        response = self.client.post('/mcp', json={
            'jsonrpc': '2.0', 'method': 'notifications/initialized'},
            headers=_headers())
        self.assertIn(response.status_code, [200, 202], response.text)
        return result

    def call(self, method, params):
        """Performs a single JSON-RPC request and returns the response."""
        response = self.client.post('/mcp', json={
            'jsonrpc': '2.0', 'id': 2, 'method': method, 'params': params,
        }, headers=_headers())
        self.assertEqual(response.status_code, 200, response.text)
        # In stateless json-response mode, the server replies with plain
        # JSON rather than with a server-sent event stream.
        self.assertTrue(response.headers['content-type'].startswith(
            'application/json'))
        return response.json()


class TestAuthenticate(McpServerTestCase):

    def test_missing_token(self):
        response = self.client.post('/mcp', json={
            'jsonrpc': '2.0', 'id': 1, 'method': 'ping', 'params': {}},
            headers={
                'MCP-Protocol-Version': PROTOCOL_VERSION,
                'Accept': 'application/json, text/event-stream'})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'invalid_token')
        self.assertIn('WWW-Authenticate', response.headers)

    def test_invalid_token(self):
        response = self.client.post('/mcp', json={
            'jsonrpc': '2.0', 'id': 1, 'method': 'ping', 'params': {}},
            headers=_headers({'Authorization': 'Bearer wrong-token'}))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'invalid_token')

    def test_valid_ping(self):
        """An authenticated JSON-RPC request that is unrelated to the
        tools (a ping) should result in a normal, empty JSON-RPC result.
        """
        result = self.call('ping', {})
        self.assertEqual(result['result'], {})


class TestInitialize(McpServerTestCase):

    def test_initialize(self):
        server_info = self.initialize()
        self.assertEqual(server_info['protocolVersion'], PROTOCOL_VERSION)
        # The server must announce that it provides tools, otherwise
        # conforming clients won't query the tools at all.
        self.assertIn('tools', server_info['capabilities'])

    def test_tools_list(self):
        self.initialize()
        tools = self.call('tools/list', {})['result']['tools']
        self.assertEqual(len(tools), 1)
        tool, = tools
        # The single tool must be properly described.
        self.assertEqual(tool['name'], 'search_documentation')
        self.assertTrue(tool['description'])
        # The tool annotations describe the tool as read-only, so that
        # clients can present it as such.
        self.assertTrue(tool['annotations']['readOnlyHint'])
        # The input schema must describe the query, and the optional
        # foundation document topics. The parameter descriptions are
        # provided through pydantic Fields, and are published in the
        # schema verbatim so that client LLMs know how to use them.
        properties = tool['inputSchema']['properties']
        self.assertIn('query', properties)
        self.assertIn('foundation_document_topics', properties)
        self.assertGreater(len(properties['query']['description']), 0)
        self.assertEqual(properties['query']['type'], 'string')
        self.assertIn('query', tool['inputSchema'].get('required', []))
        self.assertNotIn('foundation_document_topics',
                         tool['inputSchema'].get('required', []))


class TestSearchInvalidInput(McpServerTestCase):
    """Client-error cases of the search tool, which don't require the
    documentation library.
    """

    def test_empty_query(self):
        """An empty query is a client error, and should result in a tool
        error (isError) rather than in a JSON-RPC exception.
        """
        self.initialize()
        result = self.call('tools/call', {
            'name': 'search_documentation', 'arguments': {'query': ''}}
        )['result']
        self.assertTrue(result['isError'])
        self.assertIn('non-empty', result['content'][0]['text'])


@unittest.skipUnless(LIBRARY_EXISTS and HAS_API_KEY,
                     'requires the locally indexed documentation library '
                     'and an OPENAI_API_KEY')
class TestSearch(McpServerTestCase):
    """Tests that perform actual searches through the documentation
    library. These are skipped unless the library is available, so that
    the tests pass on machines without a library (and thus also on CI,
    which has no library).
    """

    def setUp(self):
        super().setUp()
        # The config may have been imported before the environment was
        # loaded by this module (when running the full test suite), in
        # which case the OpenAI API key from .env isn't part of the
        # config yet.
        key = os.environ.get('OPENAI_API_KEY')
        if key and not config.openai_api_key:
            patcher = mock.patch.object(config, 'openai_api_key', key)
            patcher.start()
            self.addCleanup(patcher.stop)

    def _call_tool(self, arguments):
        self.initialize()
        result = self.call('tools/call', {
            'name': 'search_documentation', 'arguments': arguments})
        self.assertNotIn('error', result,
                         f'JSON-RPC error: {result.get("error")}')
        return result['result']

    def test_search(self):
        result = self._call_tool({'query': SEARCH_QUERY})
        self.assertFalse(result['isError'])
        content, = result['content']
        self.assertEqual(content['type'], 'text')
        text = content['text']
        # The results should consist of documentation about keyboard
        # responses, and should include source URLs.
        self.assertIn('keyboard', text.lower())
        self.assertIn('http', text)

    def test_search_foundation_documents(self):
        """Foundation documents are included for topics of the search
        results, and for the topics that are explicitly requested.
        """
        result = self._call_tool({
            'query': SEARCH_QUERY,
            'foundation_document_topics': ['keyboard_response', 'logger'],
        })
        self.assertFalse(result['isError'])
        text = result['content'][0]['text']
        self.assertIn('keyboard', text.lower())


if __name__ == '__main__':
    unittest.main()
