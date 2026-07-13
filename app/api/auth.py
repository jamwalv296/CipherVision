from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth.google import oauth
from app.auth.jwt import create_access_token
from app.database.crud import create_user
from app.database.crud import get_user_by_google_id
from app.database.database import SessionLocal

router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={},
    )


@router.get("/login")
async def login(request: Request):

    redirect_uri = request.url_for(
        "auth_callback"
    )

    return await oauth.google.authorize_redirect(
        request,
        redirect_uri,
    )


@router.get("/auth/callback", name="auth_callback")
async def auth_callback(request: Request):

    token = await oauth.google.authorize_access_token(
        request
    )

    google_user = token["userinfo"]

    db = SessionLocal()

    try:

        user = get_user_by_google_id(
            db,
            google_user["sub"],
        )

        if user is None:

            user = create_user(
                db=db,
                google_id=google_user["sub"],
                email=google_user["email"],
                full_name=google_user["name"],
                picture_url=google_user["picture"],
            )

        access_token = create_access_token(
            str(user.id)
        )

        response = RedirectResponse(
            url="/dashboard",
            status_code=302,
        )

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=60 * 60 * 24,
        )

        return response

    finally:

        db.close()

@router.get("/logout")
async def logout():

    response = RedirectResponse(
        url="/",
        status_code=302,
    )

    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
    )

    return response