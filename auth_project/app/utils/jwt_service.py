import jwt
import datetime
from django.conf import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"


def create_tokens(user_id: int, token_version: int):
    now = datetime.datetime.utcnow()

    access_payload = {
        "user_id": user_id,
        "type": "access",
        "token_version": token_version,
        "exp": now + datetime.timedelta(minutes=15),  # короткий срок
        "iat": now,
    }

    refresh_payload = {
        "user_id": user_id,
        "type": "refresh",
        "token_version": token_version,
        "exp": now + datetime.timedelta(days=7),  # длинный срок
        "iat": now,
    }

    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm=ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm=ALGORITHM)

    return access_token, refresh_token


def decode_token(token: str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    print(f'payload: {payload}')
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
