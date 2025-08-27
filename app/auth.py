import jwt
from jwt.exceptions import InvalidTokenError
from .config import JWT_SECRET, JWT_ALG

def verify_token(token: str | None) -> dict | None:
    if not token:
        return None
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except InvalidTokenError:
        return None
