__version__ = "0.1.0"

from .client import Inboxili
from .errors import InboxiliConnectionError, InboxiliError
from .models import SendEmailResponse
from .webhooks import verify_webhook_signature

__all__ = ["Inboxili", "InboxiliError", "InboxiliConnectionError", "SendEmailResponse", "verify_webhook_signature"]
