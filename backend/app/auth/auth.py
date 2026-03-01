import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES"))  # type: ignore
assert JWT_SECRET, "JWT_SECRET must be set"
assert JWT_ALGORITHM, "JWT_ALGORITHM must be set"
assert JWT_EXPIRATION_MINUTES > 0, "JWT_EXPIRATION_MINUTES must be a positive integer"


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return str(pwd_context.hash(password))


def verify_password(plain: str, hashed: str) -> bool:
    return bool(pwd_context.verify(plain, hashed))


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    payload = {
        "sub": subject,
        "exp": expire,
    }
    return str(jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM))


def decode_access_token(token: str) -> dict:
    try:
        return dict(jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM]))
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:

    # decode access token and return user info (subject)
    return decode_access_token(credentials.credentials)
