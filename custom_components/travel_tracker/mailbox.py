"""IMAP reader. No messages or attachments are persisted."""

from __future__ import annotations

from datetime import date, timedelta
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from html.parser import HTMLParser
import imaplib
import re

from .const import LOOKBACK_DAYS, MAX_BODY_CHARS, MAX_EMAIL_BYTES, MAX_MESSAGES
from .parser import Booking, parse_confirmation


class TextFromHTML(HTMLParser):
    """HTML to text without opening links or downloading content."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in {"script", "style"}:
            self.skip += 1
        elif tag in {"p", "br", "div", "tr", "li", "td", "th"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"}:
            self.skip = max(0, self.skip - 1)
        elif tag in {"p", "div", "tr", "li", "td", "th"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip:
            self.parts.append(data)

    def text(self) -> str:
        return re.sub(r"\n[ \t]*\n+", "\n", "".join(self.parts))[:MAX_BODY_CHARS]


def _body(message: EmailMessage) -> str:
    """Prefer plain text; render HTML locally if text/plain is absent."""
    plain = html = None
    for part in (message.walk() if message.is_multipart() else (message,)):
        if part.get_content_disposition() == "attachment":
            continue
        if part.get_content_type() not in {"text/plain", "text/html"}:
            continue
        try:
            content = part.get_content()
        except (UnicodeError, LookupError, ValueError):
            continue
        if not isinstance(content, str):
            continue
        if part.get_content_type() == "text/plain" and plain is None:
            plain = content[:MAX_BODY_CHARS]
        elif part.get_content_type() == "text/html" and html is None:
            html = content[:MAX_BODY_CHARS]
    if plain is not None:
        return plain
    if html is not None:
        parser = TextFromHTML()
        parser.feed(html)
        return parser.text()
    return ""


def parse_message(raw: bytes) -> Booking | None:
    """Read a MIME message in memory and return only allowlisted itinerary fields."""
    if len(raw) > MAX_EMAIL_BYTES:
        return None
    try:
        message = BytesParser(policy=policy.default).parsebytes(raw)
        return parse_confirmation(str(message.get("From", "")),
                                  str(message.get("Subject", "")), _body(message))
    except (TypeError, ValueError, UnicodeError):
        return None


def _login(host: str, port: int, user: str, password: str, folder: str):
    account = imaplib.IMAP4_SSL(host, port, timeout=30)
    try:
        account.login(user, password)
        status, _ = account.select(folder, readonly=True)
        if status != "OK":
            raise imaplib.IMAP4.error("Cannot select folder")
        return account
    except Exception:
        try:
            account.logout()
        finally:
            raise


def test_mailbox(host: str, port: int, username: str, password: str, folder: str) -> None:
    """Verify TLS IMAP login and read-only folder access."""
    account = _login(host, port, username, password, folder)
    account.logout()


def fetch_bookings(host: str, port: int, username: str, password: str,
                   folder: str, today: date) -> list[Booking]:
    """Read a bounded selection through IMAP BODY.PEEK[] without marking it read."""
    account = _login(host, port, username, password, folder)
    try:
        since = (today - timedelta(days=LOOKBACK_DAYS)).strftime("%d-%b-%Y")
        status, messages = account.search(None, "SINCE", since)
        if status != "OK":
            raise imaplib.IMAP4.error("IMAP search failed")
        identifiers = messages[0].split()[-MAX_MESSAGES:] if messages and messages[0] else []
        bookings = []
        for identifier in identifiers:
            status, rows = account.fetch(identifier, "(BODY.PEEK[])")
            if status != "OK":
                continue
            for row in rows or ():
                if isinstance(row, tuple) and len(row) > 1 and isinstance(row[1], bytes):
                    booking = parse_message(row[1])
                    if booking:
                        bookings.append(booking)
                    break
        return bookings
    finally:
        try:
            account.logout()
        except OSError:
            pass
