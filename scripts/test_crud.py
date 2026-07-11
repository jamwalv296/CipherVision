from app.database.crud import create_user
from app.database.database import SessionLocal

db = SessionLocal()

user = create_user(
    db=db,
    google_id="123456789",
    email="test@example.com",
    full_name="Test User",
    picture_url="https://example.com/profile.jpg",
)

print(user.id)
print(user.owner_id)
print(user.email)

db.close()