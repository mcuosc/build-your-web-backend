import os
from dotenv import load_dotenv
from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, status


from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from utils.auth import auth_app
from utils.domain import domain_app
from utils.cloudflare import get_html

load_dotenv()
orgins = [
    'http://127.0.0.1:5173',
    'https://127.0.0.1',
    'https://127.0.0.1:8000',
    'http://localhost:5173',
    'https://dns.mcuosc.dev',
    'https://api.dong3.me',
    'https://api.mcuosc.dev',
    'https://dns.dong3.me',
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=orgins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=os.getenv('FASTAPI_SECRET_KEY') , max_age=86400)

app.mount('/auth', auth_app)
app.mount('/domain', domain_app)

DOMAIN = os.getenv('HOST_DOMAIN')

class domain(BaseModel):
    name: str

@app.get("/{path}")
async def read_root(path: Optional[str] = None):
    if path == None:
        return JSONResponse({'result': 'no', 'error': 'no path'}, status_code=status.HTTP_400_BAD_REQUEST)
    try:
        domain = f'{path}.{DOMAIN}'.encode('utf-8').decode('idna').lower()
        html = get_html(domain)
    except Exception as e:
        return JSONResponse({'result': 'no', 'error': str(e)}, status_code=status.HTTP_400_BAD_REQUEST)
    return HTMLResponse(content=html, status_code=status.HTTP_200_OK)
