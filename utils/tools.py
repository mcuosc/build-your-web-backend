from fastapi import Response, Cookie
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

from utils.jwt import valid_token, get_jwt_data

def set_cookie(response: Response, key: str, value: str, httponly: bool = True, max_age: int = 86400, expires: int = None, path: str = '/', domain: str = None, secure: bool = False, samesite: str = 'lax'):
    response.set_cookie(key=key, value=value, httponly=httponly, max_age=max_age, expires=expires, path=path, domain=domain, secure=secure, samesite=samesite)

def validate_token_with_cookie(user_token: str = Cookie(None)):
    try:
        if not valid_token(user_token):
            raise TokenValidationException('Invalid token')
    except Exception as e:
        raise TokenValidationException(str(e))
    return get_jwt_data(user_token)

class TokenValidationException(Exception):
    pass