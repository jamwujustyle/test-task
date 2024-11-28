from flask import Blueprint, jsonify, request
import bcrypt
import re
from database.manage_user_database import insert_into_users


class UserManagement:
    def __init__(self):
        self.blueprint = Blueprint("blueprint", __name__)
        self.register_routes()

    def register_routes(self):
        @self.blueprint.route("/users/register", methods=["POST"])
        def register():
            """register"""
            data = request.get_json()
            username = data["username"]
            email = data["email"]
            password = data["password"].encode("utf-8")

            if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
                return jsonify({"msg": "invalid email address"}), 400
            hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
            if insert_into_users("users", username, email, password):
                return jsonify({"msg": "user successfully registered"}), 201
            else:
                return jsonify({"msg": "error registering user"}), 500

        @self.blueprint.route("/users/authenticate", methods="POST")
        def authenticate():
            """authenticate"""
            data = request.get_json()
            email = data["email"]

        @self.blueprint.route("/users/login", methods=["POST"])
        def login():
            """loigin"""
            data = request.get_json()
            email = data["email"]
            password = data["password"]
