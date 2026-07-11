import secrets

from sqlalchemy.orm import Session

from app.database.models import User


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