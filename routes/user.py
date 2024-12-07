from flask import Blueprint, jsonify, request, current_app
import bcrypt
from queries.db_queries import insert_into_users, select_from_table
from db import connect
from psycopg2.extras import DictCursor
from email_verification.verification import handle_email_verification
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    get_jwt,
)


SECRET_KEY = "24e2b6bb0774463e890d1ad7d562c801"


class UserManagement:
    #######################  INIT ROUTING  ########################
    def __init__(self, app=None):
        self.blueprint = Blueprint("user-management", __name__)
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
                identity=user[2], additional_claims={"role": user[4]}
            )
            return jsonify({"access token": access_token}), 201

        @self.blueprint.route("/users/verify", methods=["POST"])

        #############################   TODO
        # def verify():
        #     data = request.get_json()
        #     email = data.get("email")
        #     if email != "Unknown" and select_from_table("users", email=email):
        #         handle_email_verification(email)
        #         return jsonify({"msg": "found the user"})
        #     else:
        #         return jsonify({"msg": "user not found"}), 404

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

        @self.blueprint.route("/users/get", methods=["GET"])
        @jwt_required()
        def get_all_users():
            """fetches all users from table "users" """
            claims = get_jwt()
            current_app.logger.debug(f"claims: {claims}")
            if claims.get("role") != "admin":
                return jsonify({"error": "access denied"}), 401
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
            claims = get_jwt()
            current_app.logger.debug(f"claims: {claims}")
            query = "SELECT * FROM users WHERE id = %s"
            if claims.get("role") != "admin":
                return jsonify({"error": "access denied"}), 401
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
                return jsonify({"error": "invalid data"}), 400

            username = data.get("username")
            role = data.get("role")

            claims = get_jwt()
            if claims.get("role") != "admin":
                return jsonify({"msg": "access denied"}), 401

            if not username and not role:
                return jsonify({"error": "missing required arguments"}), 400
            query = "UPDATE users SET "
            update_fields = []
            params = []
            if username:
                update_fields.append("username = %s")
                params.append(username)
            if role:
                update_fields.append("role = %s")
                params.append(role)
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

            try:
                id = int(id)
            except ValueError as ve:
                return jsonify({"err": "value error"}), 400
            current_app.logger.debug(f"id is: {id} and the type is: {type(id)}")
            """UPDATES USER PARTIALLY"""
            data = request.get_json()
            if not data:
                return jsonify({"error": "invalid request"}), 400
            username = data.get("username")
            role = data.get("role")
            if username and role:
                current_app.logger.debug("request is taken")

            if not role or not username:
                return jsonify({"error": "missing required arguments"}), 400

            claims = get_jwt()
            if claims:
                current_app.logger.debug("claims are taken")

            if claims.get("role") != "admin":
                return jsonify({"error": "access denied"}), 401
            query = "UPDATE users SET "

            update_fields = []
            params = []

            if username:
                update_fields.append("username = %s")
                params.append(username)
            if role:
                update_fields.append("role = %s")
                params.append(role)
            query += ", ".join(update_fields) + " WHERE id = %s"
            params.append(id)
            try:
                with connect() as conn:
                    cursor = conn.cursor(cursor_factory=DictCursor)
                    cursor.execute(query, tuple(params))

                    if cursor.rowcount == 0:
                        return jsonify({"error": "empty request"}), 422
                    new_data = select_from_table("users", id=id)
                    current_app.logger.debug(f"new data: {new_data}")
                    current_app.logger.debug(f"id passed: {id} Type: {type(id)}")
                    conn.commit()
                    return (
                        jsonify(
                            {
                                "msg": "User updated",
                                "username": new_data["username"],
                                "role": new_data["role"],
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
            claims = get_jwt()
            if claims:
                current_app.logger.debug("claims are taken")
            if claims.get("role") != "admin":
                return jsonify({"error": "access denied"}), 401
            user = select_from_table("users", id=id)
            if not user:
                return jsonify({"error": "user not found"}), 404
            query = "DELETE from users WHERE id = %s"
            current_app.logger.debug(f"type of user {type(user)}")
            try:
                with connect() as conn:
                    cursor = conn.cursor(cursor_factory=DictCursor)
                    cursor.execute(
                        query,
                        (id,),
                    )
                    conn.commit()
                    return jsonify({"deleted": user}), 201
            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

    def register_blueprint(self, app):
        app.register_blueprint(self.blueprint)
