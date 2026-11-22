from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SendEmailResponse:
    #: ``"sent"``: the delivery provider accepted the message (HTTP 200), which is not the same as reaching the inbox.
    #: ``"queued"``: the key is sending faster than 100 emails a minute, so the email was accepted (HTTP 202) and will be
    #: delivered in order shortly. Treat it as success and do not send it again.
    status: str
    #: ``None`` while queued.
    message_id: Optional[str]
    #: Set when queued. It appears as ``queue_id`` on this email's later webhook events.
    queue_id: Optional[str] = None
