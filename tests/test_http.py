"""Offline checks for the anonymous Render deployment."""

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("DUFFEL_API_KEY_LIVE", "offline-test-placeholder")

from starlette.testclient import TestClient
from flights.server import configure_http, mcp


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.dict(os.environ, {"RENDER_EXTERNAL_HOSTNAME": "example.onrender.com"}):
            configure_http()
        cls.client = TestClient(mcp.streamable_http_app())
        cls.client.__enter__()
        cls.addClassCleanup(cls.client.__exit__, None, None, None)
        cls.headers = {
            "host": "example.onrender.com",
            "accept": "application/json, text/event-stream",
        }

    def test_anonymous_discovery(self):
        response = self.client.post("/mcp", headers=self.headers, json={
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                       "clientInfo": {"name": "test", "version": "1"}},
        })
        self.assertEqual(response.status_code, 200)
        response = self.client.post("/mcp", headers=self.headers, json={
            "jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {},
        })
        self.assertEqual(response.status_code, 200)
        tools = response.json()["result"]["tools"]
        self.assertEqual({t["name"] for t in tools}, {
            "search_flights", "get_offer_details", "search_multi_city",
        })
        for tool in tools:
            self.assertTrue(tool["annotations"]["readOnlyHint"])
            self.assertEqual(tool["_meta"]["securitySchemes"], [{"type": "noauth"}])

    def test_health(self):
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})

    def test_untrusted_host_and_origin(self):
        for headers, status in [
            (dict(self.headers, host="untrusted.example"), 421),
            (dict(self.headers, origin="https://untrusted.example"), 403),
        ]:
            self.assertEqual(self.client.post("/mcp", headers=headers, json={}).status_code, status)


if __name__ == "__main__":
    unittest.main()
