import uuid
import os
from fastapi import FastAPI, Cookie, HTTPException, Request, status, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from authlib.integrations.starlette_client import OAuth, OAuthError
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError, DecodeError

from utils.tools import validate_token_with_cookie, TokenValidationException
from utils.jwt import create_token, valid_token


auth_app = FastAPI()

GCP_CLIENT_ID = os.getenv('GCP_CLIENT_ID')
GCP_CLIENT_SECRET = os.getenv('GCP_CLIENT_SECRET')
FRONTEND_URL = ''
BACKEND_CALLBACK_URL = ''

if os.getenv('ENV') == 'dev':
    FRONTEND_URL = f'http://{os.getenv("DEV_FRONTEND_DOMAIN")}'
    BACKEND_CALLBACK_URL = f'https://{os.getenv("DEV_BACKEND_DOMAIN")}/auth/login/callback'
else:
    FRONTEND_URL = f'https://{os.getenv("FRONTEND_DOMAIN")}'
    BACKEND_CALLBACK_URL = f'https://{os.getenv("BACKEND_DOMAIN")}/auth/login/callback'

oauth = OAuth()
oauth.register(
    name='google',
    client_id=GCP_CLIENT_ID,
    client_secret=GCP_CLIENT_SECRET,
    authorize_params=None,
    refresh_token_url=None,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile', 'prompt': 'select_account'},
)


@auth_app.exception_handler(TokenValidationException)
async def token_validation_exception_handler(request: Request, exc: TokenValidationException):
    response = JSONResponse({'result': 'no', 'error': str(exc)}, status_code=status.HTTP_401_UNAUTHORIZED)
    request.session['user_token'] = ''
    response.delete_cookie('user_token')
    return response

@auth_app.get('/logout')
async def logout(request: Request):
    response = RedirectResponse(url=FRONTEND_URL, status_code=status.HTTP_302_FOUND)
    response.set_cookie('user_token', '', samesite='none', secure=True, max_age=0, httponly=True)
    return response

@auth_app.get('/login')
async def login(request: Request, user_token: str = Cookie(None)):
    print('login', user_token)
    try:
        if user_token and valid_token(user_token):
            print('user_token', user_token)
            red_url = f'{FRONTEND_URL}/create'
            return RedirectResponse(url=red_url, status_code=status.HTTP_302_FOUND,\
                                    )
    except Exception as e:
        pass

    state = str(uuid.uuid4())
    # request.session['state'] = state
    respone = await oauth.google.authorize_redirect(request, BACKEND_CALLBACK_URL, state=state, prompt="select_account")
    return respone

@auth_app.get('/login/callback')
async def login_callback(request: Request, user_token: str = Cookie(None)):
    state_from_session = request.session.get('state')
    state_from_query = request.query_params.get('state')
    
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as error:
        return JSONResponse({'result': 'no', 'error': str(error)})
    
    user_token = create_token(token['userinfo']['email'])
    red_url = f'{FRONTEND_URL}/create'
    response = RedirectResponse(url=red_url, status_code=status.HTTP_302_FOUND)

    response.set_cookie('user_token', user_token, samesite='none', secure=True, max_age=86400, httponly=True)
    return response

@auth_app.get('/validate')
async def valid(user_data: dict = Depends(validate_token_with_cookie)):
    return JSONResponse({'result': 'ok'})
    
