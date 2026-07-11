import os
import tempfile

from fastapi import APIRouter
from fastapi import File
from fastapi import UploadFile
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth.jwt import get_user_id
from app.database.database import SessionLocal
from app.database.models import User
from app.services.detect_service import DetectService
from app.services.payload_decoder import PayloadDecoder

router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)

decoder = PayloadDecoder()


@router.get("/verify", response_class=HTMLResponse)
async def verify_page(request: Request):

    token = request.cookies.get("access_token")

    if token is None:
        return RedirectResponse("/")

    if get_user_id(token) is None:
        return RedirectResponse("/")

    return templates.TemplateResponse(
        request=request,
        name="verify.html",
        context={},
    )


@router.post("/verify")
async def verify_image(
    request: Request,
    file: UploadFile = File(...),
):

    token = request.cookies.get("access_token")

    if token is None:
        return RedirectResponse("/")

    if get_user_id(token) is None:
        return RedirectResponse("/")

    suffix = os.path.splitext(file.filename)[1].lower()

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    ) as temp:

        temp.write(await file.read())

        image_path = temp.name

    bits = DetectService.extract(image_path)

    result = decoder.decode(bits)

    if result is None:

        return templates.TemplateResponse(
            request=request,
            name="verify.html",
            context={
                "error": "Unable to verify ownership.",
            },
        )

    owner_id = result["identifier"]

    db = SessionLocal()

    try:

        user = (
            db.query(User)
            .filter(User.owner_id == owner_id)
            .first()
        )

        if user is None:

            return templates.TemplateResponse(
                request=request,
                name="verify.html",
                context={
                    "error": "Owner not found.",
                },
            )

        return templates.TemplateResponse(
            request=request,
            name="verify.html",
            context={
                "verified": True,
                "name": user.full_name,
                "email": user.email,
                "picture": user.picture_url,
            },
        )

    finally:

        db.close()