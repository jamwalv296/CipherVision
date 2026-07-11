from app.auth.jwt import create_access_token
from app.auth.jwt import get_user_id

token = create_access_token("123456")

print(token)

print()

print(get_user_id(token))