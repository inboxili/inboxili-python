from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SendEmailResponse:
    #: ``"sent"`` means the delivery provider accepted the message, not that it reached the inbox.
    status: str
    message_id: Optional[str]
