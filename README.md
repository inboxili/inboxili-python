# inboxili (Python)

Python client for the [Inboxili](https://inboxili.com) transactional email API. No dependencies, Python 3.9+, type hints included.

```bash
pip install inboxili
```

## Send an email

```python
import os
from inboxili import Inboxili

client = Inboxili(os.environ["INBOXILI_API_KEY"])

result = client.emails.send(
    to="ada@example.com",
    from_email="hello@yourdomain.com",  # must be a sender on a verified domain
    from_name="Acme",
    subject="Welcome, {{first_name}}",
    html_body="<p>Hi {{first_name}}, your account is ready.</p>",
    text_body="Hi Ada, your account is ready.",
    template_data={"first_name": "Ada"},
)
print(result.status, result.message_id)
```

`status == "sent"` means the delivery provider accepted the message, not that it reached the inbox. Use webhooks for delivery events.

### From a template

```python
client.emails.send(
    to="ada@example.com",
    from_email="hello@yourdomain.com",
    template_id="00000000-0000-0000-0000-000000000000",
    template_data={"first_name": "Ada"},
)
```

## Authentication

Create an API key in the dashboard under Settings, Developer, with the `transactional:send` scope. Load it from the environment or a secret manager. Never commit it.

## Options

```python
Inboxili(api_key, base_url="https://api.inboxili.com/api/v1", timeout=10.0, max_retries=2)
```

## Error handling

```python
from inboxili import InboxiliError, InboxiliConnectionError

try:
    client.emails.send(...)
except InboxiliError as e:
    print(e.status, e.code, e.message)   # e.g. 422 sender_not_verified
except InboxiliConnectionError:
    ...  # no response; the email may or may not have been sent
```

| Status | `code` | Meaning |
|---|---|---|
| 401 | `unauthorized` | Missing, invalid, revoked or expired key |
| 403 | `forbidden` | Missing scope, or IP not allowed |
| 422 | `validation_error`, `sender_not_verified`, `send_failed` | Bad request, unverified sender, or provider rejection |
| 429 | `rate_limited` | Over 120 requests per minute for this key |

**Retries.** Only HTTP 429 is retried (`max_retries`, default 2), because the request was rejected before sending. Timeouts and 5xx are never retried: the API has no idempotency key, so a retry could send a duplicate.

## Webhooks

```python
from inboxili import verify_webhook_signature

ok = verify_webhook_signature(raw_body_bytes, request.headers["X-Inboxili-Signature"], os.environ["INBOXILI_WEBHOOK_SECRET"])
```

Pass the raw body bytes, not a re-serialised object.

## Limits of the API

One recipient per request. No attachments, CC, BCC or reply-to fields. No scheduling. See the [API reference](https://inboxili.com/transactional-email-api).

## Development

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

## Links

[Documentation](https://inboxili.com/docs) · [Python guide](https://inboxili.com/integrations/python) · [Report a vulnerability](SECURITY.md) · MIT licensed
