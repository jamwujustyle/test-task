import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app


def create_jwt_token(id):
    payload = {"sub": id, "exp": datetime.utcnow() + timedelta(hours=1)}
    return jwt.encode(payload, "igjddigoj", algorithm="HS256")


def decode_jwt_token(token):
    secret_key = current_app.config["SECRET_KEY"]
    return jwt.decode(token, secret_key, algorithms="HS256")


def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")

        current_app.logger.debug(f"Authorization token: {token}")

        if not token:
            return jsonify({"msg": "no token"}), 404
        if token.startswith("Bearer"):
            token = token.split(" ")[1]
        else:
            return jsonify({"msg": "invalid format"}), 400

        try:
            payload = decode_jwt_token(token)
            current_app.logger.debug(f"token payload: : {payload}")
        except Exception as ex:
            return jsonify({"msg": "invalid or expired token"}), 401
        return func(payload, *args, **kwargs)

    return decorated
