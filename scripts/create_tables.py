from app.database.database import Base
from app.database.database import engine

import app.database.models

Base.metadata.create_all(bind=engine)

print("Tables created successfully.")