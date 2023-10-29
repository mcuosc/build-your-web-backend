import os
from typing import Optional
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request, status, Depends

from utils.cloudflare import get_domain, update_html, get_html, modify_domain_data
from utils.tools import validate_token_with_cookie, TokenValidationException

domain_app = FastAPI()
HOME_URL = os.getenv('HOST_URL')
HOST_DOMAIN = os.getenv('HOST_DOMAIN')

@domain_app.exception_handler(TokenValidationException)
async def token_validation_exception_handler(request: Request, exc: TokenValidationException):
    response = JSONResponse({'result': 'no', 'error': str(exc)}, status_code=status.HTTP_401_UNAUTHORIZED)
    request.session['user_token'] = ''
    response.delete_cookie('user_token')
    return response

@domain_app.get('/')
async def get_domain_list(user_data: dict = Depends(validate_token_with_cookie)):
    domain_list = get_domain(user_data['email'])
    return JSONResponse({'result': 'ok', 'domain_list': domain_list})

class AddDomain(BaseModel):
    domain: str

@domain_app.post('/')
async def add_domain(items: AddDomain, user_data: dict = Depends(validate_token_with_cookie)):
    domain_name = items.domain.lower()
    current_domain_list = get_domain(user_data['email'])
    if len(current_domain_list) >= 3:
        return JSONResponse({'result': 'no', 'error': '最多三個歐 >w<'}, status_code=status.HTTP_400_BAD_REQUEST)

    try:
        modify_domain_data(domain_name, user_data['email'], 'POST')
    except Exception as e:
        return JSONResponse({'result': 'no', 'error': str(e)}, status_code=status.HTTP_400_BAD_REQUEST)
    return JSONResponse({'result': 'ok'})

class DelDomain(BaseModel):
    domain: str

@domain_app.delete('/')
async def del_domain(items: DelDomain, user_data: dict = Depends(validate_token_with_cookie)):
    domain_name = items.domain.lower()
    try:
        modify_domain_data(domain_name, user_data['email'], 'DELETE')
    except Exception as e:
        return JSONResponse({'result': 'no', 'error': str(e)}, status_code=status.HTTP_400_BAD_REQUEST)
    return JSONResponse({'result': 'ok'})

class EditHtml(BaseModel):
    domain: str
    html: str

@domain_app.put('/')
async def edit_content(items: EditHtml, user_data: dict = Depends(validate_token_with_cookie)):
    domain_name = items.domain.lower()
    html = items.html
    try:
        update_html(domain_name, html)
    except Exception as e:
        return JSONResponse({'result': 'no', 'error': str(e)}, status_code=status.HTTP_400_BAD_REQUEST)
    return JSONResponse({'result': 'ok'})

@domain_app.get('/html/{path}')
async def read_root(path: str):
    path = f'{path}.{HOST_DOMAIN}'
    try:
        html = get_html(path)
    except Exception as e:
        return JSONResponse({'result': 'no', 'error': str(e)})
    return JSONResponse({'result': 'ok', 'html': html})
