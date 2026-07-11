from uuid import UUID

from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth.jwt import get_user_id
from app.database.database import SessionLocal
from app.database.models import User

router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):

    token = request.cookies.get(
        "access_token"
    )

    if token is None:

        return RedirectResponse(
            "/"
        )

    user_id = get_user_id(
        token
    )

    if user_id is None:

        return RedirectResponse(
            "/"
        )

    db = SessionLocal()

    try:

        user = (
            db.query(User)
            .filter(
                User.id == UUID(user_id)
            )
            .first()
        )

        if user is None:

            return RedirectResponse(
                "/"
            )

        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "user": user,
            },
        )

    finally:

        db.close()