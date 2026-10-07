import hashlib
import hmac
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from inboxili import Inboxili, InboxiliConnectionError, InboxiliError, verify_webhook_signature


class Stub(BaseHTTPRequestHandler):
    responses = []  # list of (status, body) consumed in order
    seen = []

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        Stub.seen.append((self.path, dict(self.headers), json.loads(self.rfile.read(length))))
        status, body = Stub.responses.pop(0)
        raw = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):
        pass


class ClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), Stub)
        cls.url = f"http://127.0.0.1:{cls.server.server_port}/api/v1"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        Stub.responses, Stub.seen = [], []

    def client(self, **kw):
        return Inboxili("ik_live_test", base_url=self.url, **kw)

    def test_send_maps_request_and_response(self):
        Stub.responses = [(200, {"status": "sent", "message_id": "m1"})]
        out = self.client().emails.send(
            to="a@b.co", from_email="hi@x.co", subject="S", html_body="<p>{{n}}</p>", template_data={"n": 1}
        )
        self.assertEqual((out.status, out.message_id), ("sent", "m1"))
        path, headers, body = Stub.seen[0]
        self.assertEqual(path, "/api/v1/transactional/send")
        self.assertEqual(headers["Authorization"], "Bearer ik_live_test")
        self.assertEqual(
            body, {"to": "a@b.co", "from_email": "hi@x.co", "subject": "S", "html_body": "<p>{{n}}</p>", "template_data": {"n": 1}}
        )

    def test_validation_happens_before_request(self):
        c = self.client()
        with self.assertRaises(ValueError):
            c.emails.send(to="a@b.co", from_email="x@y.co", subject="s")
        with self.assertRaises(ValueError):
            c.emails.send(to="a@b.co", from_email="x@y.co", html_body="x")
        self.assertEqual(Stub.seen, [])

    def test_api_error(self):
        Stub.responses = [(422, {"error": {"code": "sender_not_verified", "message": "nope"}})]
        with self.assertRaises(InboxiliError) as cm:
            self.client().emails.send(to="a@b.co", from_email="x@y.co", subject="s", html_body="x")
        self.assertEqual((cm.exception.status, cm.exception.code, str(cm.exception)), (422, "sender_not_verified", "nope"))

    def test_retries_429_only(self):
        Stub.responses = [(429, {"error": {"code": "rate_limited", "message": "slow"}}), (200, {"status": "sent", "message_id": None})]
        out = self.client(max_retries=1).emails.send(to="a@b.co", from_email="x@y.co", template_id="t")
        self.assertIsNone(out.message_id)
        self.assertEqual(len(Stub.seen), 2)

        Stub.responses, Stub.seen = [(500, {}), (200, {"status": "sent"})], []
        with self.assertRaises(InboxiliError):
            self.client().emails.send(to="a@b.co", from_email="x@y.co", template_id="t")
        self.assertEqual(len(Stub.seen), 1)

    def test_connection_error(self):
        c = Inboxili("k", base_url="http://127.0.0.1:1/api/v1", timeout=1)
        with self.assertRaises(InboxiliConnectionError):
            c.emails.send(to="a@b.co", from_email="x@y.co", template_id="t")

    def test_repr_hides_key(self):
        self.assertNotIn("ik_live_test", repr(self.client()))

    def test_webhook_signature(self):
        body = b'{"event":"delivered"}'
        sig = hmac.new(b"s3cret", body, hashlib.sha256).hexdigest()
        self.assertTrue(verify_webhook_signature(body, sig, "s3cret"))
        self.assertFalse(verify_webhook_signature(body, sig, "other"))
        self.assertFalse(verify_webhook_signature(body + b" ", sig, "s3cret"))


if __name__ == "__main__":
    unittest.main()
