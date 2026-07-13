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
from app.services.detect_service import DetectService
from app.services.payload_decoder import PayloadDecoder
from app.database.crud import get_user_by_owner_id

router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)

encoder = PayloadEncoder()
decoder = PayloadDecoder()

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

        decoded = None

        try:

            bits = DetectService.extract(
                input_path
            )

            decoded = decoder.decode(
                bits
            )

        except Exception:

            decoded = None

        if decoded is not None:

            existing_owner = get_user_by_owner_id(
                db,
                decoded["identifier"],
            )

            if existing_owner is not None:

                if existing_owner.id == user.id:

                    return templates.TemplateResponse(
                        request=request,
                        name="embed.html",
                        context={
                            "info": "This image is already protected by your CipherVision account.",
                        },
                    )

                return templates.TemplateResponse(
                    request=request,
                    name="embed.html",
                    context={
                        "error": f"This image already belongs to {existing_owner.full_name}. Embedding another watermark is not permitted.",
                    },
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