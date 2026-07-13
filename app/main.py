from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.dashboard import router as dashboard_router
from app.api.auth import router as auth_router
from app.api.embed import router as embed_router
from app.api.verify import router as verify_router
import os

from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

load_dotenv()

app = FastAPI(
    title="CipherVision",
    version="1.0.0",
)

limiter = Limiter(
    key_func=get_remote_address
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)

app.add_middleware(
    SlowAPIMiddleware
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("JWT_SECRET"),
)

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)

templates = Jinja2Templates(
    directory="app/templates"
)

app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(embed_router)
app.include_router(verify_router)