import os
import jwt
from jwt.exceptions import DecodeError, ExpiredSignatureError
from fastapi import Depends
from datetime import datetime
from datetime import timedelta
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer

API_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
API_ALGORITHM = os.getenv('JWT_ALGORITHM') or 'HS256'
API_EXPIRE_MINUTES = 60

oauth_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Could not validate credentials',
    headers={'WWW-Authenticate': 'Bearer'},
)

def valid_email(email: str):
    domain = email.split('@')[1]
    vaild_email_list = [
        'me.mcu.edu.tw',
        'ms1.mcu.edu.tw',
    ]
    if domain in vaild_email_list:
        return True
    return False

def create_access_token(*, data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=API_EXPIRE_MINUTES)
    email = data.get('email', '')
    if not valid_email(email):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')
    to_encode.update({'exp': expire})

    encoded_jwt = jwt.encode(to_encode, API_SECRET_KEY, algorithm=API_ALGORITHM)
    return encoded_jwt

def create_token(email):
    data = {'email': email}
    return create_access_token(data=data)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, API_SECRET_KEY, algorithms=[API_ALGORITHM])
    except DecodeError:
        return None
    except ExpiredSignatureError:
        return None
    return payload

def valid_token(token: str):
    payload = decode_token(token)
    if payload == None:
        return False
    email: str = payload.get('email', '')
    return valid_email(email)

def get_jwt_data(token: str):
    payload = decode_token(token)
    if payload == None:
        return False
    return payload