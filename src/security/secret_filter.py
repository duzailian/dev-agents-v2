import re
import logging

logger = logging.getLogger(__name__)

class SecretFilter:
    """
    Filters sensitive information from text using regex patterns.
    """

    # Patterns to match sensitive data assignments
    # Matches key assignment followed by quoted value or unquoted value
    PATTERNS = [
        # Standard sensitive field names with quoted values
        r'(password\s*=\s*)(["\'][^"\']+["\'])',
        r'(api[_-]?key\s*=\s*)(["\'][^"\']+["\'])',
        r'(token\s*=\s*)(["\'][^"\']+["\'])',
        r'(secret\s*=\s*)(["\'][^"\']+["\'])',
        r'(credential\s*=\s*)(["\'][^"\']+["\'])',
        r'(auth\s*=\s*)(["\'][^"\']+["\'])',
        r'(private[_-]?key\s*=\s*)(["\'][^"\']+["\'])',
        r'(access[_-]?key\s*=\s*)(["\'][^"\']+["\'])',
        r'(client[_-]?secret\s*=\s*)(["\'][^"\']+["\'])',
        # Unquoted values (less common but possible)
        r'(password\s*=\s*)([^\s\'"]+)',
        r'(api[_-]?key\s*=\s*)([^\s\'"]+)',
        r'(token\s*=\s*)([^\s\'"]+)',
        r'(secret\s*=\s*)([^\s\'"]+)',
        # AWS/Cloud specific
        r'(aws[_-]?access[_-]?key[_-]?id\s*=\s*)(["\'][^"\']+["\'])',
        r'(aws[_-]?secret[_-]?access[_-]?key\s*=\s*)(["\'][^"\']+["\'])',
        # Database connection strings
        r'(db[_-]?password\s*=\s*)(["\'][^"\']+["\'])',
        r'(connection[_-]?string\s*=\s*)(["\'][^"\']+["\'])',
    ]

    @classmethod
    def filter(cls, text: str) -> str:
        """
        Redacts sensitive information from the input text.

        Args:
            text: The input string (e.g., log message, prompt).

        Returns:
            The text with sensitive values replaced by [REDACTED].
        """
        filtered_text = text
        for pattern in cls.PATTERNS:
            def replacement(m):
                # Log that a redaction occurred (without logging the secret)
                key_part = m.group(1).strip()
                logger.debug(f"Redacting sensitive value for key: {key_part}")
                return f"{m.group(1)}'[REDACTED]'"

            filtered_text = re.sub(pattern, replacement, filtered_text, flags=re.IGNORECASE)

        return filtered_text
