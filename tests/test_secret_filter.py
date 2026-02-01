import pytest
from src.security.secret_filter import SecretFilter

class TestSecretFilter:
    def test_filter_password(self):
        text = "user='admin', password='super_secret_password', other='value'"
        filtered = SecretFilter.filter(text)
        assert "password='[REDACTED]'" in filtered
        assert "super_secret_password" not in filtered
        assert "user='admin'" in filtered

    def test_filter_api_key(self):
        text = 'config = { "api_key": "abc12345", "timeout": 30 }'
        filtered = SecretFilter.filter(text)
        # Note: The regex might need adjustment depending on exact requirement,
        # but let's test the specific patterns requested.
        # Pattern requested: api[_-]?key\s*=\s*["'][^"']+["']
        # The example in task description: api_key='abc' -> api_key='[REDACTED]'

        text2 = "api_key='abc12345'"
        filtered2 = SecretFilter.filter(text2)
        assert "api_key='[REDACTED]'" in filtered2
        assert "abc12345" not in filtered2

    def test_filter_token(self):
        text = 'auth_token = "deadbeef"'
        filtered = SecretFilter.filter(text)
        # Pattern requested: token\s*=\s*["'][^"']+["']
        text_strict = 'token="deadbeef"'
        filtered_strict = SecretFilter.filter(text_strict)
        # Check that it is redacted. The implementation standardizes to single quotes.
        assert "token='[REDACTED]'" in filtered_strict
        assert "deadbeef" not in filtered_strict

    def test_normal_text(self):
        text = "This is a normal log message with value=10."
        assert SecretFilter.filter(text) == text

    def test_multiple_replacements(self):
        text = "password='pwd' and api_key='key'"
        filtered = SecretFilter.filter(text)
        assert "password='[REDACTED]'" in filtered
        assert "api_key='[REDACTED]'" in filtered
        assert "'pwd'" not in filtered
        # "key" is present in "api_key", so we must check for the quoted value
        assert "'key'" not in filtered
