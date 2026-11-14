"""Shared integration constants."""

DOMAIN = "travel_tracker"
PLATFORMS = ("sensor", "binary_sensor")
CONF_FOLDER = "folder"
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_FOLDER = "INBOX"
DEFAULT_PORT = 993
DEFAULT_SCAN_INTERVAL = 30
MIN_SCAN_INTERVAL = 15
MAX_SCAN_INTERVAL = 240
LOOKBACK_DAYS = 365
MAX_MESSAGES = 300
MAX_EMAIL_BYTES = 512 * 1024
MAX_BODY_CHARS = 150_000

# Optional, explicitly selected Mail and Packages configuration reference
MAIL_AND_PACKAGES_DOMAIN = "mail_and_packages"
CONF_SOURCE = "source"
CONF_LINKED_ENTRY_ID = "linked_entry_id"
SOURCE_IMAP = "imap"
SOURCE_LINKED = "mail_and_packages"
