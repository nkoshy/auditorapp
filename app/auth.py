import secrets
from typing import Optional

# In-memory user store
USERS = {
    "alice": "alice123",
    "bob": "bob123",
}

# token -> username
_tokens: dict[str, str] = {}


def authenticate(username: str, password: str) -> Optional[str]:
    if USERS.get(username) == password:
        token = secrets.token_hex(32)
        _tokens[token] = username
        return token
    return None


def get_user_from_token(token: str) -> Optional[str]:
    return _tokens.get(token)
