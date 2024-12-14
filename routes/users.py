from flask import Blueprint, jsonify, request, current_app
import bcrypt
from datetime import timedelta
from queries.db_queries import (
    insert_into_users,
    select_from_table,
    delete_records_from_table,
)
from db import connect
from psycopg2.extras import DictCursor

# from email_verification.verification import handle_email_verification
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    get_jwt,
)
from routes.util.utils import (
    email_validation,
    check_for_admin,
    append_update_field,
    reset_sequence_id,
    append_for_patch,
)
from collections import OrderedDict

SECRET_KEY = "24e2b6bb0774463e890d1ad7d562c801"


class UserManagement:
    #######################  INIT ROUTING  ########################
    def __init__(self, app=None):
        self.blueprint = Blueprint("user-management", __name__)
        self.table_name = "users"
        if app is not None:
            self.register_blueprint(app)

        #######################  ENDPOINTS  ########################

        @self.blueprint.route("/users/register", methods=["POST"])
        def register():

            data = request.get_json()

            if not data:
                return (jsonify({"msg": "invalid data"}), 400)
            username = data.get("username")
            email = data.get("email")
            email_check = email_validation(email)
            if email_check is None:
                return jsonify({"error": "failed email check"}), 400
            password = data.get("password")
            role = data.get("role", "user")

            if not username or not email or not password:
                return jsonify({"msg": "missing required arguments"}), 400

            hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
            try:
                is_success = insert_into_users(
                    "users", username, email, hashed_password.decode("utf-8"), role
                )
                if is_success:
                    return jsonify({"msg": "registered successfully"}), 201
                else:
                    return jsonify({"msg": "user already exists"}), 400
            except Exception as ex:
                return (jsonify({"msg": "error inserting into database"}), 500)

        @self.blueprint.route("/users/login", methods=["POST"])
        def login():

            data = request.get_json()
            if not data:
                return jsonify({"error": "bad request"}), 403
            # username = data["username"]
            if not data.get("email") or not data.get("password"):
                return jsonify({"error": "missing email or password"}), 403
            email = data["email"]
            user = select_from_table("users", email=email)
            if not user:
                return jsonify({"error": "user with that email does not exist"}), 404
            access_token = create_access_token(
                identity=user["email"],
                additional_claims={"role": user["role"]},
                expires_delta=timedelta(hours=12),
            )
            return jsonify({"access token": f"Bearer {access_token}"}), 201

        @self.blueprint.route("/users/verify", methods=["POST"])
        @self.blueprint.route("/users/me", methods=["GET"])
        @jwt_required()
        def get_current_user():
            email = get_jwt_identity()
            if not email:
                return jsonify({"msg": "user id not found in token "}), 400
            user = select_from_table("users", email=email)

            if not user:
                return jsonify({"msg": "user not found"}), 404

            return jsonify(
                OrderedDict(
                    [
                        ("id", user["id"]),
                        ("username", user["username"]),
                        ("email", user["email"]),
                        ("role", user["role"]),
                    ]
                )
            )

        @self.blueprint.route("/users/get", methods=["GET"])
        @jwt_required()
        def get_all_users():
            """fetches all users from table "users" """
            query = "SELECT * FROM users;"
            with connect() as conn:
                cursor = conn.cursor(cursor_factory=DictCursor)
                cursor.execute(query)
                users = cursor.fetchall()

                users_data = [
                    {
                        "id": user["id"],
                        "username": user["username"],
                        "email": user["email"],
                        "role": user["role"],
                    }
                    for user in users
                ]

                return (
                    jsonify({"users": users_data}),
                    201,
                )

        @self.blueprint.route("/users/get/<id>", methods=["GET", "POST"])
        @jwt_required()
        def get_user_by_id(id):
            """get user by id"""

            query = "SELECT * FROM users WHERE id = %s"
            with connect() as conn:
                cursor = conn.cursor(cursor_factory=DictCursor)
                cursor.execute(query, (id,))
                user = cursor.fetchone()
                conn.commit()
                if not user:
                    return jsonify({"error": "user does not exist"}), 400
                return (
                    jsonify(
                        {
                            "id": user["id"],
                            "username": user["username"],
                            "email": user["email"],
                            "role": user["role"],
                        }
                    ),
                    201,
                )

        @self.blueprint.route("/users/put/<id>", methods=["PUT"])
        @jwt_required()
        def put(id):
            """ "update user by id"""
            data = request.get_json()
            if not data:
                return jsonify({"error": "empty request body"}), 400

            username = data.get("username")
            role = data.get("role")
            email = data.get("email")
            password = data.get("password")

            check_for_admin()
            if email_validation(email) is not True:
                return email_validation(email)

            if any(not value for value in [email, password]):
                return jsonify({"error": "missing required arguments"}), 400
            hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
            query = "UPDATE users SET "
            update_fields = []
            params = []
            append_update_field(update_fields, params, "username", username)
            append_update_field(update_fields, params, "role", role)
            append_update_field(update_fields, params, "email", email)
            append_update_field(
                update_fields, params, "password", hashed_password.decode("utf-8")
            )
            query += ", ".join(update_fields) + " WHERE id = %s"
            params.append(id)

            if not update_fields:
                return (jsonify({"msg": "no fields to update"}), 400)
            try:
                with connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, tuple(params))
                    conn.commit()

                    if cursor.rowcount == 0:
                        return jsonify({"error": "user not found"}), 404

                    return jsonify({"msg": "user updated successfully"}), 200
            except Exception as ex:
                return jsonify({"error": ex}), 500

        @self.blueprint.route("/users/patch/<id>", methods=["PATCH"])
        @jwt_required()
        def patch(id):
            """UPDATES USER PARTIALLY"""
            check_for_admin()
            try:
                id = int(id)
            except ValueError as ve:
                return jsonify({"err": "value error"}), 400
            data = request.get_json()
            if not data:
                return jsonify({"error": "empty request body"}), 400
            username = data.get("username")
            email = data.get("email")
            if email is not None and email_validation(email) is not True:
                return email_validation(email)
            role = data.get("role")
            password = data.get("password")
            if password is not None:
                hashed_password = bcrypt.hashpw(
                    password.encode("utf-8"), bcrypt.gensalt()
                )
                append_for_patch(
                    update_fields, params, "password", hashed_password.decode("utf-8")
                )
            query = f"UPDATE {self.table_name} SET "
            update_fields = []
            params = []

            append_for_patch(update_fields, params, "username", username)

            append_for_patch(update_fields, params, "role", role)
            append_for_patch(update_fields, params, "email", email)
            query += ", ".join(update_fields) + " WHERE id = %s"
            params.append(id)
            if not update_fields:
                return jsonify({"error": "no fields to update"}), 400
            try:
                with connect() as conn:
                    cursor = conn.cursor(cursor_factory=DictCursor)
                    cursor.execute(query, tuple(params))
                    updated_user = select_from_table(self.table_name, id=id)

                    if cursor.rowcount == 0:
                        return jsonify({"error": "empty request"}), 422
                    conn.commit()
                    return (
                        jsonify(
                            {
                                "user updated": updated_user,
                            }
                        ),
                        200,
                    )

            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

        @self.blueprint.route("/users/delete/<id>", methods=["DELETE"])
        @jwt_required()
        def delete(id):
            """deletes by user id"""
            check_for_admin()
            user = select_from_table(self.table_name, id=id)
            if not user:
                return jsonify({"error": "user not found"}), 404
            try:
                result = delete_records_from_table(self.table_name, id=id)
                if result is True:
                    reset_sequence_id(self.table_name)
                    return jsonify({"deleted": user}), 201
            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

    def register_blueprint(self, app):
        app.register_blueprint(self.blueprint)
