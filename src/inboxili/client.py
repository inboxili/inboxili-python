import json
import random
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from . import __version__
from .errors import InboxiliConnectionError, InboxiliError
from .models import SendEmailResponse

DEFAULT_BASE_URL = "https://api.inboxili.com/api/v1"


class Emails:
    def __init__(self, client: "Inboxili"):
        self._client = client

    def send(
        self,
        *,
        to: str,
        from_email: str,
        from_name: Optional[str] = None,
        subject: Optional[str] = None,
        html_body: Optional[str] = None,
        text_body: Optional[str] = None,
        template_id: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
    ) -> SendEmailResponse:
        """Send one transactional email.

        Provide ``html_body`` or ``template_id``. ``subject`` is required unless a template is used.
        ``text_body`` does not get merge tags applied by the API.
        """
        if not html_body and not template_id:
            raise ValueError("Provide either html_body or template_id.")
        if not template_id and not subject:
            raise ValueError("subject is required when not using a template.")

        payload = {
            "to": to,
            "from_email": from_email,
            "from_name": from_name,
            "subject": subject,
            "html_body": html_body,
            "text_body": text_body,
            "template_id": template_id,
            "template_data": template_data,
        }
        body = self._client._post("/transactional/send", {k: v for k, v in payload.items() if v is not None})
        return SendEmailResponse(status=str(body.get("status")), message_id=body.get("message_id"))


class Inboxili:
    """Client for the Inboxili transactional email API.

    Only HTTP 429 is retried (up to ``max_retries`` times) because the request was rejected before sending.
    Timeouts and 5xx are never retried: the API has no idempotency key, so a retry could send a duplicate.
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 10.0,
        max_retries: int = 2,
    ):
        if not api_key:
            raise ValueError("api_key is required.")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self.emails = Emails(self)

    def __repr__(self) -> str:  # never print the key
        return f"Inboxili(base_url={self._base_url!r})"

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        data = json.dumps(payload).encode()
        attempt = 0
        while True:
            req = urllib.request.Request(
                self._base_url + path,
                data=data,
                method="POST",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": f"inboxili-python/{__version__}",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    return json.loads(resp.read() or b"{}")
            except urllib.error.HTTPError as e:
                try:
                    body = json.loads(e.read() or b"{}")
                except ValueError:
                    body = {}
                if e.code == 429 and attempt < self._max_retries:
                    time.sleep(2**attempt + random.random() * 0.25)
                    attempt += 1
                    continue
                err = body.get("error") or {}
                raise InboxiliError(e.code, err.get("code", "http_error"), err.get("message", e.reason)) from None
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                raise InboxiliConnectionError(
                    "No response from Inboxili. The email may or may not have been sent."
                ) from e
