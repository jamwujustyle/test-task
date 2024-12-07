from flask import Blueprint, jsonify, request, current_app
from db import connect
from flask_jwt_extended import create_access_token, jwt_required, get_jwt
from psycopg2.extras import DictCursor
from queries.db_queries import (
    select_from_table,
    insert_into_users,
    insert_into_categories,
)


class CategoryManagement:
    ###########################INIT ROUTING################################
    def __init__(self, app=None):
        self.blueprint = Blueprint("category-management", __name__)
        self.table_name = "categories"
        if app is not None:
            self.register_blueprint(app)

        ###################### ENDPOINTS #####################
        @self.blueprint.route("/categories/post", methods=["POST"])
        @jwt_required()
        def post():
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
            # if not parent_category_id:
            #     current_app.logger.debug("missing parent id")
            #     return jsonify({"error": "missing required arguments"}), 400
            claims = get_jwt()
            if claims.get("role") != "admin":
                current_app.logger.debug("access denied: insufficient permissions")
                return jsonify({"error": "access denied"}), 403
            try:
                parent_category_id = (
                    int(parent_category_id) if parent_category_id is not None else None
                )
            except ValueError:
                return jsonify({"error": ValueError}), 400
            # query = insert_into_categories = (
            #     f"INSERT INTO {table_name} (name, description, parent_category_id) VALUES (%s, %s, %s) ON CONFLICT (name) DO NOTHING"
            # )
            try:
                # with connect() as conn:
                #     cursor = conn.cursor(cursor_factory=DictCursor)
                #     cursor.execute(
                #         query,
                #         (
                #             name,
                #             description,
                #             parent_category_id,
                #         ),
                #     )
                #     conn.commit()
                category_id = insert_into_categories(
                    "categories",
                    name=name,
                    description=description,
                    parent_category_id=parent_category_id,
                )
                if category_id:
                    current_app.logger.debug(
                        f"successfully inserted into table {self.table_name} with id of {category_id}"
                    )
                    return jsonify({"msg": "category has been created "}), 201
                else:
                    current_app.logger.debug(
                        f"category with name {name} already exists"
                    )
                    return jsonify({"error": "category name already exists"}), 409
            except Exception as ex:
                current_app.logger.debug("error manipulating database")
                return jsonify({"error": str(ex)}), 400

        @self.blueprint.route("/categories/get", methods=["GET"])
        def get_all_categories():
            query = f"SELECT * FROM {self.table_name};"
            try:
                with connect() as conn:
                    cursor = conn.cursor(cursor_factory=DictCursor)
                    cursor.execute(query)
                    categories = cursor.fetchall()
                    if categories:
                        categories_data = [
                            {
                                "id": category["id"],
                                "name": category["name"],
                                "description": category["description"],
                                "parent_category_id": category["parent_category_id"],
                                "created_at": category["created_at"],
                                "updated_at": category["updated_at"],
                            }
                            for category in categories
                        ]
                        return jsonify({"categories": categories_data})
                    else:
                        return (
                            jsonify(
                                {"error": "error retrieving categories from table"}
                            ),
                            500,
                        )

            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

        @self.blueprint.route("/categories/patch/<id>", methods=["PATCH"])
        @jwt_required()
        def patch(id):
            data = request.get_json()
            name = data.get("name")
            description = data.get("description")
            updated_at = data.get("updated_at")
            if not name and not description:
                current_app.logger.debug(
                    "missing required arguments. at least 1 fields is neede to update"
                )
                return jsonify({"error": "missing arguments"}), 400
            claims = get_jwt()
            if claims.get("role") != "admin":
                current_app.logger.debug(
                    "insuffisient permissions. role 'admin' required"
                )
                return jsonify({"error": "access denied"}), 409
            update_fields = []
            params = []
            query = f"UPDATE {self.table_name} SET "
            try:
                if name:
                    update_fields.append("name = %s")
                    params.append(name)
                if description:
                    update_fields.append("description = %s")
                    params.append(description)
            except Exception as ex:
                return jsonify({"error": str(ex)}), 422
            query += ", ".join(update_fields) + " WHERE id = %s"
            params.append(id)
            try:
                with connect() as conn:
                    cursor = conn.cursor(cursor_factory=DictCursor)
                    cursor.execute(
                        query,
                        tuple(params),
                    )
                    if cursor.rowcount == 0:
                        return (
                            jsonify(
                                {f"error": "error inserting into table {table_name}"}
                            ),
                            400,
                        )

                    new_data = select_from_table(self.table_name, id=id)
                    current_app.logger.debug(
                        f"new data: {new_data}\nid passed: {id} type of id {type(id)}"
                    )
                    conn.commit()
                    return (
                        jsonify(
                            {
                                "msg": "user updated",
                                "name": name,
                                "description": description,
                                "updated_at": updated_at,
                            }
                        ),
                        200,
                    )

            except Exception as ex:
                current_app.logger.debug(
                    f"error occured during insertion into {self.table_name}"
                )
                return jsonify({"error": str(ex)}), 500

    def register_blueprint(self, app):
        app.register_blueprint(self.blueprint)
