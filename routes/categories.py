from flask import Blueprint, jsonify, request, current_app
from db import connect
from flask_jwt_extended import jwt_required
from psycopg2.extras import DictCursor
from queries.db_queries import (
    select_from_table,
    insert_into_table,
    delete_records_from_table,
)
from routes.util.utils import (
    check_for_admin,
    append_update_field,
    reset_sequence_id,
    append_for_patch,
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
            check_for_admin()
            data = request.get_json()
            if not data:
                return jsonify({"error": "bad request"}), 400
            name = data.get("name")
            description = data.get("description")
            parent_category_id = data.get("parent_category_id")
            if any(not value for value in [name, description, parent_category_id]):
                return jsonify({"error": "missing required arguments"}), 400
            try:
                category_id = insert_into_table(
                    "categories",
                    name=name,
                    description=description,
                    parent_category_id=parent_category_id,
                )
                if category_id:

                    return jsonify({"msg": "category has been created "}), 201
                else:

                    return jsonify({"error": "category name already exists"}), 409
            except Exception as ex:
                current_app.logger.debug("error manipulating database")
                return jsonify({"error": str(ex)}), 400

        @self.blueprint.route("/categories/get", methods=["GET"])
        def get_all_categories():
            try:
                categories = select_from_table(self.table_name)
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
                return (
                    jsonify({"error": "error retrieving categories from table"}),
                    500,
                )
            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

        @self.blueprint.route("/categories/get/<id>", methods=["GET"])
        def get_category_by_id(id):
            try:
                category = select_from_table(self.table_name, id=id)
                if category:
                    return (
                        jsonify(
                            {
                                "name": category.get("name"),
                                "description": category.get("description"),
                                "parent_category_id": category.get(
                                    "parent_category_id"
                                ),
                                "created_at": category.get("created_at"),
                                "updated_at": category.get("updated_at"),
                            }
                        ),
                        200,
                    )
                else:
                    return jsonify({"error": "could not find category at this id"}), 404
            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

        @self.blueprint.route("/categories/put/<id>", methods=["PUT"])
        @jwt_required()
        def put(id):
            check_for_admin()
            data = request.get_json()
            if not data:
                return jsonify({"error": "invalid json format"})
            name = data.get("name")
            description = data.get("description")
            parent_category_id = data.get("parent_category_id")
            updated_at = data.get("updated_at")

            if any(not value for value in [name, parent_category_id]):
                return (
                    jsonify(
                        {
                            "error": "missing required arguments (name, parent_category_id)"
                        }
                    ),
                    400,
                )

            query = "UPDATE categories SET "
            update_fields = []
            params = []
            append_update_field(update_fields, params, "name", name)
            append_update_field(update_fields, params, "description", description)
            append_update_field(
                update_fields, params, "parent_category_id", parent_category_id
            )
            append_update_field(update_fields, params, "updated_at", None)
            if not update_fields:
                return jsonify({"error": "no fields to update"}), 400

            query += ", ".join(update_fields) + " WHERE id = %s"
            params.append(id)

            try:
                with connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    if cursor.rowcount == 0:
                        return jsonify({"error": "insertion into table failed"}), 400
                    conn.commit()
                    cursor.execute(
                        f"select updated_at from {self.table_name} where id = %s", (id,)
                    )
                    updated_at = cursor.fetchone()
                    return jsonify(
                        {
                            "msg": "category updated",
                            "name": name,
                            "description": description,
                            "updated_at": updated_at,
                        }
                    )
            except Exception as ex:
                return jsonify({"outer error": str(ex)}), 500

        @self.blueprint.route("/categories/patch/<id>", methods=["PATCH"])
        @jwt_required()
        def patch(id):
            check_for_admin()
            data = request.get_json()
            if not data:
                return jsonify({"error": "empty request body"}), 400
            name = data.get("name")
            description = data.get("description")
            parent_category_id = data.get("parent_category_id")
            updated_at = data.get("updated_at")
            if all(not value for value in [name, description, parent_category_id]):
                return jsonify({"error": "missing required arguments"}), 400
            update_fields = []
            params = []
            query = f"UPDATE {self.table_name} SET "
            try:
                append_for_patch(update_fields, params, "name", name)
                append_for_patch(update_fields, params, "description", description)
                append_for_patch(update_fields, params, "updated_at", None)
                append_for_patch(
                    update_fields, params, "parent_category_id", parent_category_id
                )

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
                            jsonify({f"error": "error inserting into table "}),
                            400,
                        )

                    conn.commit()
                    new_data = select_from_table(self.table_name, id=id)
                    return (
                        jsonify(
                            {
                                "msg": "user updated",
                                "name": new_data["name"],
                                "description": new_data["description"],
                                "updated at": new_data["updated_at"],
                                "parent category id": new_data["parent_category_id"],
                            }
                        ),
                        200,
                    )

            except Exception as ex:

                return jsonify({"error": str(ex)}), 500

        def reset_id_sequence():
            query = f"""
                SELECT setval(
                            pg_get_serial_sequence('{self.table_name}', 'id'),
                            (SELECT MAX(id) FROM {self.table_name}),
                            false
                            );
                            """
            try:
                with connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query)
                    conn.commit()
            except Exception as ex:
                current_app.logger.debug(f"error resetting id sequence {str(ex)}")

        @self.blueprint.route("/categories/delete/<id>", methods=["DELETE"])
        @jwt_required()
        def delete(id):
            check_for_admin()
            try:
                category_to_delete = select_from_table(self.table_name, id=id)
                if category_to_delete:
                    current_app.logger.debug(
                        f"fetched the category with id: {category_to_delete.get('id')}"
                    )
                else:
                    current_app.logger.debug("category does not exists")
                    return jsonify({"error": "category does not exist"}), 404
            except Exception as ex:
                return jsonify({"error fetching category": str(ex)}), 500
            try:
                if delete_records_from_table(self.table_name, id=id):

                    category_to_delete = select_from_table(self.table_name, id=id)
                    if not category_to_delete:
                        current_app.logger.debug(
                            f"deleted successfully: {category_to_delete}"
                        )
                        reset_id_sequence()
                        return jsonify({"category deleted": category_to_delete}), 200

            except Exception as ex:
                return jsonify({"error from outer-most": str(ex)}), 500

    def register_blueprint(self, app):
        app.register_blueprint(self.blueprint)
