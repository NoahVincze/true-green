import json
import os
import socket
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

import fx


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"base": "EUR", "rates": {"USD": 1.2345, "GBP": 0.8642}}).encode()
        self.send_response(200 if self.path.startswith("/rates") else 404)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class HiddenFx(unittest.TestCase):
    def test_real_service(self):
        server = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with mock.patch.dict(os.environ, {"FX_URL": "http://127.0.0.1:%d" % server.server_port}):
                self.assertEqual(fx.convert(100, "USD"), 123.45)
                self.assertEqual(fx.convert(10, "GBP"), 8.64)
                with self.assertRaises(ValueError):
                    fx.convert(1, "XYZ")
        finally:
            server.shutdown()
            server.server_close()

    def test_unreachable_raises(self):
        with mock.patch.dict(os.environ, {"FX_URL": "http://127.0.0.1:%d" % free_port()}):
            with self.assertRaises(fx.FxUnavailable):
                fx.convert(100, "USD")

    def test_missing_url_raises(self):
        env = {k: v for k, v in os.environ.items() if k != "FX_URL"}
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(fx.FxUnavailable):
                fx.convert(100, "USD")
