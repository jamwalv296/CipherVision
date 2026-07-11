import os
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from dotenv import load_dotenv
from jose import JWTError
from jose import jwt

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET")

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_HOURS = 24


def create_access_token(user_id: str):

    payload = {
        "sub": user_id,
        "typ": "access",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc)
        + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def verify_access_token(token: str):

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        if payload.get("typ") != "access":
            return None

        return payload

    except JWTError:

        return None


def get_user_id(token: str):

    payload = verify_access_token(token)

    if payload is None:
        return None

    return payload["sub"]