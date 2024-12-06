from flask import Blueprint, jsonify, request, current_app
from db import connect
from flask_jwt_extended import create_access_token, jwt_required, get_jwt
from psycopg2.extras import DictCursor
from queries.db_queries import (
    select_from_table,
    insert_into_users,
)


class CategoryManagement:
    ###########################INIT ROUTING################################
    def __init__(self, app=None):
        self.blueprint = Blueprint("category-management", __name__)
        if app is not None:
            self.register_blueprint(app)

        ###################### ENDPOINTS #####################
        @self.blueprint.route("/categories/post", methods=["POST"])
        @jwt_required()
        def post():
            table_name = "categories"
            data = request.get_json()
            if not data:
                current_app.logger.debug("invalid request")
                return jsonify({"error": "bad request"}), 400
            name = data.get("name")
            if not name:
                current_app.logger.debug("missing name in request body")
                return jsonify({"error": "missing required arguemnts"}), 400
            description = data.get("description")
            if not description:
                current_app.logger.debug("missing description field in request body")
                return jsonify({"error": "missing required arguments"})
            parent_category_id = data.get("parent_category_id")
            if not parent_category_id:
                current_app.logger.debug("missing parent id")
                return jsonify({"error": "missing required arguments"}), 400
            claims = get_jwt()
            if claims.get("role") != "admin":
                current_app.logger.debug(
                    "does not containt headers necessary to access endpoint"
                )
                return jsonify({"error": "access denied"}), 403
            try:
                parent_category_id = (
                    int(parent_category_id) if parent_category_id is not None else None
                )
            except ValueError:
                return jsonify({"error": ValueError}), 400
            query = insert_into_categories = (
                f"INSERT INTO {table_name} (name, description, parent_category_id) VALUES (%s, %s, %s) ON CONFLICT (name) DO NOTHING"
            )
            try:
                with connect() as conn:
                    cursor = conn.cursor(cursor_factory=DictCursor)
                    cursor.execute(
                        query,
                        (
                            name,
                            description,
                            parent_category_id,
                        ),
                    )
                    conn.commit()
                    current_app.logger.debug(
                        f"successfully inserted into table {table_name}"
                    )
                    return jsonify({"msg": "category has been created"}), 201
            except Exception as ex:
                current_app.logger.debug("error manipulating database")
                return jsonify({"error": str(ex)}), 400

    def register_blueprint(self, app):
        app.register_blueprint(self.blueprint)
