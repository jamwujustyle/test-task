import jwt
from datetime import datetime, timedelta


def create_jwt_token(user_id):
    payload = {"sub": user_id, "exp": datetime.utcnow() + timedelta(hours=1)}
    return jwt.encode(payload, "igjddigoj", algorithm="HS256")


def decode_jwt_token(token, secret_key):
    return jwt.decode(token, secret_key, algorithms="HS256")
