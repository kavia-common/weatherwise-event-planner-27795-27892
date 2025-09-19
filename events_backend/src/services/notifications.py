import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from src.core.config import get_settings


@dataclass(frozen=True)
class EmailMessage:
    """Value object representing an email to be sent."""
    to: str
    subject: str
    body: str
    sender: Optional[str] = None


class EmailService(ABC):
    """
    PUBLIC_INTERFACE
    Abstract provider-agnostic email service.

    Concrete implementations may use SMTP, a SaaS provider, or any custom transport.
    """

    @abstractmethod
    def send(self, message: EmailMessage) -> None:
        """
        PUBLIC_INTERFACE
        Send a single email message.

        Implementations must raise exceptions for non-transient, caller-actionable errors.
        Transient errors can be retried internally or propagated as exceptions.
        """
        raise NotImplementedError


class ConsoleEmailService(EmailService):
    """
    PUBLIC_INTERFACE
    Default 'console logger' email service.

    This implementation simply logs the intended message using the 'notifications.email'
    logger, making it safe for environments without configured email providers.
    """

    def __init__(self) -> None:
        self._logger = logging.getLogger("notifications.email")

    def send(self, message: EmailMessage) -> None:
        """Log the message to the application logs (stdout)."""
        sender = message.sender or get_settings().EMAIL_SENDER or "no-reply@example.com"
        # Single-line compact log entry to keep CI logs readable
        self._logger.info(
            "[EMAIL_STUB] From=%s | To=%s | Subject=%s | Body=%s",
            sender,
            message.to,
            message.subject,
            message.body,
        )


# Module-level default provider getter
def get_email_service() -> EmailService:
    """
    PUBLIC_INTERFACE
    Resolve and return the current EmailService implementation.

    This is intentionally simple and returns the ConsoleEmailService by default.
    To plug in a real provider, replace the return value with an instance of a concrete service
    (e.g., SmtpEmailService) using configuration flags from Settings.
    """
    # Future: consult env flags in Settings to choose provider type
    return ConsoleEmailService()
