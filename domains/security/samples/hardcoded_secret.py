# Vulnerable example: Hardcoded secrets
# WARNING: This is intentionally vulnerable code for educational purposes only.
# All values below are FAKE and for demonstration only.

SECRET_KEY = "fake_secret_123_do_not_use"
API_KEY = "sk-fake-key-do-not-use-in-production"
DATABASE_PASSWORD = "admin123_fake"


def get_config():
    """Return application configuration with embedded secrets."""
    return {
        "secret": SECRET_KEY,
        "api_key": API_KEY,
        "db_pass": DATABASE_PASSWORD,
        "debug": False,
    }


def connect_to_service():
    """Simulate connecting to a service using hardcoded credentials."""
    token = "ghp_fakeTokenValue1234567890abcdef"
    return {"Authorization": f"Bearer {token}"}
