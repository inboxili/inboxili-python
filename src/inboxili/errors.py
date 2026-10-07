class InboxiliError(Exception):
    """Raised for any non-2xx response from the Inboxili API."""

    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        #: Machine-readable code from the API, for example ``sender_not_verified``.
        self.code = code
        self.message = message

    def __repr__(self) -> str:
        return f"InboxiliError(status={self.status}, code={self.code!r}, message={self.message!r})"


class InboxiliConnectionError(Exception):
    """Raised when no response was received (network failure or timeout).

    The email may or may not have been sent.
    """
