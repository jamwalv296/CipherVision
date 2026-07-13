import secrets

from sqlalchemy.orm import Session

from app.database.models import User
from app.database.models import Watermark

def generate_owner_id():

    return secrets.token_hex(8).upper()


def get_user_by_google_id(
    db: Session,
    google_id: str,
):

    return (
        db.query(User)
        .filter(User.google_id == google_id)
        .first()
    )


def get_user_by_owner_id(
    db: Session,
    owner_id: str,
):

    return (
        db.query(User)
        .filter(User.owner_id == owner_id)
        .first()
    )


def create_user(
    db: Session,
    google_id: str,
    email: str,
    full_name: str,
    picture_url: str,
):

    while True:

        owner_id = generate_owner_id()

        existing = get_user_by_owner_id(
            db,
            owner_id,
        )

        if existing is None:
            break

    user = User(
        google_id=google_id,
        email=email,
        full_name=full_name,
        picture_url=picture_url,
        owner_id=owner_id,
    )

    db.add(user)

    db.commit()

    db.refresh(user)

    return user

def create_watermark(
    db: Session,
    user_id,
    filename: str,
    owner_identifier: str,
):

    watermark = Watermark(
        user_id=user_id,
        filename=filename,
        owner_identifier=owner_identifier,
    )

    db.add(watermark)

    db.commit()

    db.refresh(watermark)

    return watermark


def get_user_watermarks(
    db: Session,
    user_id,
):

    return (
        db.query(Watermark)
        .filter(Watermark.user_id == user_id)
        .order_by(Watermark.created_at.desc())
        .all()
    )


def increment_verified_count(
    db: Session,
    owner_identifier: str,
):

    watermark = (
        db.query(Watermark)
        .filter(
            Watermark.owner_identifier == owner_identifier
        )
        .order_by(
            Watermark.created_at.desc()
        )
        .first()
    )

    if watermark is None:

        return

    watermark.verified_count += 1

    db.commit()