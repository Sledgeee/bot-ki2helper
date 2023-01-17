import os
from typing import Union, Any

import db
from jose.exceptions import JWTClaimsError
from jose import jwt, JWTError, ExpiredSignatureError


ALGORITHM = os.getenv("JWT_ALG")
JWT_ACCESS_SECRET_KEY = os.getenv("JWT_ACCESS_SECRET_KEY")


def authorized(token: Union[str, Any] = None):
    if token is None:
        return False
    try:
        payload = jwt.decode(token, JWT_ACCESS_SECRET_KEY, ALGORITHM)
        if db.sessions.get(payload["sub"]) is not None:
            return True
        return False
    except JWTClaimsError:
        return False
    except ExpiredSignatureError:
        return False
    except JWTError:
        return False
