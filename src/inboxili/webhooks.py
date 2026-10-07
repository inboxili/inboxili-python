import hashlib
import hmac
from typing import Union


def verify_webhook_signature(raw_body: Union[bytes, str], signature: str, secret: str) -> bool:
    """Verify an ``X-Inboxili-Signature`` header.

    ``raw_body`` must be the exact bytes received, not re-serialised JSON. ``signature`` is the hex HMAC-SHA256
    of the body keyed with the webhook's secret.
    """
    if isinstance(raw_body, str):
        raw_body = raw_body.encode()
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.strip().lower())
