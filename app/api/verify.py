import os
import tempfile
from PIL import Image
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
from slowapi import Limiter
from slowapi.util import get_remote_address


limiter = Limiter(
    key_func=get_remote_address
)

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
@limiter.limit("20/minute")
@router.post("/verify")
async def verify_image(
    request: Request,
    file: UploadFile = File(...),
):
    token = request.cookies.get("access_token")
    if token is None:
        return RedirectResponse("/")
    current_user_id = get_user_id(token)
    if current_user_id is None:
        return RedirectResponse("/")
    suffix = os.path.splitext(file.filename)[1].lower()
    MAX_FILE_SIZE = 20 * 1024 * 1024
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        return templates.TemplateResponse(
            request=request,
            name="verify.html",
            context={
                "error": "Image size must not exceed 20 MB.",
            },
        )
    await file.seek(0)
    if suffix not in [".png", ".jpg", ".jpeg"]:
        return templates.TemplateResponse(
            request=request,
            name="verify.html",
            context={
                "error": "Please upload a PNG or JPEG image.",
            },
        )
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    ) as temp:
        temp.write(await file.read())
        image_path = temp.name
    try:
        with Image.open(image_path) as img:
            img.verify()
    except Exception:
        os.remove(image_path)
        return templates.TemplateResponse(
            request=request,
            name="verify.html",
            context={
                "error": "The uploaded file is not a valid PNG or JPEG image.",
            },
        )
    try:
        bits = DetectService.extract(
            image_path
        )
        result = decoder.decode(
            bits
        )
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
            owner = (
                db.query(User)
                .filter(User.owner_id == owner_id)
                .first()
            )
            if owner is None:
                return templates.TemplateResponse(
                    request=request,
                    name="verify.html",
                    context={
                        "error": "Owner not found.",
                    },
                )
            is_owner = str(owner.id) == current_user_id
            return templates.TemplateResponse(
                request=request,
                name="verify.html",
                context={
                    "verified": True,
                    "is_owner": is_owner,
                    "name": owner.full_name,
                    "email": owner.email,
                    "picture": owner.picture_url,
                },
            )
        finally:
            db.close()
    except Exception:
        return templates.TemplateResponse(
            request=request,
            name="verify.html",
            context={
                "error": "Unable to verify ownership.",
            },
        )
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)