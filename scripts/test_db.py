from sqlalchemy import text

from app.database.database import SessionLocal

db = SessionLocal()

try:

    result = db.execute(
        text("SELECT version();")
    )

    print(result.scalar())

finally:

    db.close()