from flask import Blueprint, jsonify, request, current_app
import bcrypt
import re
from queries.db_queries import insert_into_users, select_from_table
from db import connect
from email_verification.verification import handle_email_verification
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    JWTManager,
)


SECRET_KEY = "24e2b6bb0774463e890d1ad7d562c801"


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
            username = data["username"]
            email = data["email"]
            user = select_from_table("users", email=email)
            if not user:
                return jsonify({"error": "user with that email does not exist"}), 404
            access_token = create_access_token(identity=email)
            return jsonify({"access token": access_token}), 201

        @self.blueprint.route("/users/verify", methods=["POST"])
        def verify():
            data = request.get_json()
            email = data.get("email")
            if email != "Unknown" and select_from_table("users", email=email):
                handle_email_verification(email)
                return jsonify({"msg": "found the user"})
            else:
                return jsonify({"msg": "user not found"}), 404

        @self.blueprint.route("/users/me", methods=["GET"])
        @jwt_required()
        def get_current_user():
            data = request.get_json()
            email = data.get("email")
            id = get_jwt_identity()
            if not id:
                return jsonify({"msg": "user id not found in token "}), 400
            user = select_from_table("users", email=email)

            if not user:
                return jsonify({"msg": "user not found"}), 404
            return jsonify(
                {
                    "msg": "access granted",
                    "id": id,
                    "username": user[1],
                    "email": user[2],
                }
            )

    def register_blueprint(self, app):
        app.register_blueprint(self.blueprint)
