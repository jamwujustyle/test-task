from flask import Blueprint, jsonify, request, current_app
import bcrypt
import re
from db_queries import insert_into_users, select_from_table
from db import connect
from verification import handle_email_verification
from jwt_utils import create_jwt_token, decode_jwt_token
import jwt


class UserManagement:
    #######################  INIT ROUTING  ########################
    def __init__(self, app=None):
        self.blueprint = Blueprint("auth", __name__)
        if app is not None:
            self.register_blueprint(app)

        #######################  ENDPOINTS  ########################

        @self.blueprint.route("/users/register", methods=["POST"])
        def register():

            data = request.get_json()

            if not data:
                return (jsonify({"msg": "invalid data"}), 400)

            username = data["username"]
            email = data["email"]
            password = data["password"]

            if not username or not email or not password:
                return jsonify({"msg": "missing required arguments"}), 500

            hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
            try:
                is_success = insert_into_users(
                    "users", username, email, hashed_password.decode("utf-8")
                )
                if is_success:
                    return jsonify({"msg": "registered successfully"}), 201
                else:
                    return jsonify({"msg": "user already exists"})
            except Exception as ex:
                return (jsonify({"msg": "error inserting into database"}), 500)

        @self.blueprint.route("/users/login", methods=["POST"])
        def login():

            data = request.get_json()

            email = data.get("email")
            password = data.get("password")
            query = "SELECT * FROM users WHERE email = %s"

            with connect() as conn:
                user = select_from_table("users", email)
                if not user:
                    return jsonify({"msg": "user not found"}), 404

                stored_password = user[3]

                if bcrypt.checkpw(
                    password.encode("utf-8"), stored_password.encode("utf-8")
                ):
                    token = create_jwt_token({"user_id": user[0]})
                    return jsonify({"msg": "loged in", "token": token}), 200
                else:
                    return jsonify({"msg": "invalid credentials"}), 400

        @self.blueprint.route("/users/verify", methods=["POST"])
        def verify():
            data = request.get_json()
            email = data.get("email")
            if email != "Unknown" and select_from_table("users", email):
                handle_email_verification(email)
                return jsonify({"msg": "found the user"})
            else:
                return jsonify({"msg": "user not found"}), 404

        @self.blueprint.route("/users/me", methods=["POST"])
        def get_current_user():
            token = request.headers.get("Authorization")
            current_app.logger.debug(f"Authorization token: {token}")

            if not token:
                return jsonify({"msg": "could not find token"}), 404

            try:
                parts = token.split(" ")
                if len(parts) != 2 or parts[0] != "Bearer":
                    return jsonify({"msg": "invalid authorization header format"}), 401

                # Decode the token
                try:
                    decoded_token = decode_jwt_token(token, "igjddigoj")
                except jwt.ExpiredSignatureError:
                    return jsonify({"msg": "token has expired"}), 401
                except jwt.InvalidTokenError:
                    return jsonify({"msg": "invalid token"}), 401

                user_id = decoded_token.get("user_id")
                if not user_id:
                    return jsonify({"msg": "failed decoding token"}), 401

                # Query the database
                query = "SELECT * FROM users WHERE id = %s"
                with connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, (user_id,))
                    user = cursor.fetchone()

                    if user:
                        user_info = {
                            "id": user[0],
                            "username": user[1],
                            "email": user[2],
                        }
                        return jsonify({"msg": user_info}), 200
                    else:
                        return jsonify({"msg": "user not found"}), 404

            except Exception as ex:
                current_app.logger.error(f"Error in /users/me: {ex}")
                return jsonify({"msg": "invalid token"}), 401

    def register_blueprint(self, app):
        app.register_blueprint(self.blueprint)
