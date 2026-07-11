import os
import tempfile
from uuid import UUID

from fastapi import APIRouter
from fastapi import File
from fastapi import Request
from fastapi import UploadFile
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth.jwt import get_user_id
from app.database.database import SessionLocal
from app.database.models import User
from app.services.embed_service import EmbedService
from app.services.payload_encoder import PayloadEncoder

router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)

encoder = PayloadEncoder()


@router.get("/embed", response_class=HTMLResponse)
async def embed_page(request: Request):

    token = request.cookies.get("access_token")

    if token is None:
        return RedirectResponse("/")

    user_id = get_user_id(token)

    if user_id is None:
        return RedirectResponse("/")

    return templates.TemplateResponse(
        request=request,
        name="embed.html",
        context={},
    )


@router.post("/embed")
async def embed_image(
    request: Request,
    file: UploadFile = File(...),
):

    token = request.cookies.get("access_token")

    if token is None:
        return RedirectResponse("/")

    user_id = get_user_id(token)

    if user_id is None:
        return RedirectResponse("/")

    db = SessionLocal()

    try:

        user = (
            db.query(User)
            .filter(User.id == UUID(user_id))
            .first()
        )

        if user is None:
            return RedirectResponse("/")

        suffix = os.path.splitext(file.filename)[1].lower()

        if suffix not in [".png", ".jpg", ".jpeg"]:
            return {"error": "Unsupported image format"}

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_input:

            temp_input.write(
                await file.read()
            )

            input_path = temp_input.name

        output_path = input_path.replace(
            suffix,
            f"_watermarked{suffix}",
        )

        payload = encoder.encode(
            user.owner_id
        )

        EmbedService.embed(
            input_path,
            output_path,
            payload,
        )

        return FileResponse(
            output_path,
            filename="watermarked.png",
            media_type="image/png",
        )

    finally:

        db.close()