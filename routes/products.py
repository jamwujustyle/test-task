from flask import Blueprint, current_app, request, jsonify
from flask_jwt_extended import get_jwt, jwt_required
from db import connect
from psycopg2.extras import DictCursor
from queries.db_queries import select_from_table, delete_records_from_table
from routes.util.utils import (
    check_for_admin,
    reset_sequence_id,
    destructuring_utility,
    append_update_field,
    append_for_patch,
)


class ProductManagement:
    def __init__(self, app=None):
        self.blueprint = Blueprint("product_management", __name__)
        self.table_name = "products"
        if app is not None:
            self.register_blueprint(self.blueprint(app))

        @self.blueprint.route("/products/post", methods=["POST"])
        @jwt_required()
        def post():
            check_for_admin()
            data = request.get_json()
            if not data:
                return jsonify({"error": "missinq required arguments"}), 400

            name = data.get("name")
            description = data.get("description")
            category_id = data.get("category_id")
            price = data.get("price")
            if any(not value for value in [name, category_id, price]):
                return jsonify({"error": "missing required arguments"}), 400
            query = f"""INSERT INTO {self.table_name} (name, description, category_id, price) VALUES (%s, %s, %s, %s) RETURNING name, description, category_id, price;"""
            params = [name, description, category_id, price]
            try:
                with connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    result = cursor.fetchone()
                    if not result:
                        return jsonify({"error": "found nothing"}), 404
                    conn.commit()
                    return (
                        jsonify({"msg": result}),
                        201,
                    )
            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

        @self.blueprint.route("/products/get", methods=["GET"])
        def get_all_products():
            try:
                products = select_from_table(self.table_name)
                if products is None:
                    return jsonify({"error": "no products to fetch"}), 404
                return jsonify({"products": destructuring_utility(products)})

            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

        @self.blueprint.route("/products/get/<id>", methods=["GET"])
        def get_by_id(id):
            try:
                product = select_from_table(self.table_name, id=id)
                if product is None:
                    return jsonify({"error": "product not found"}), 404
                return jsonify({"product": destructuring_utility(product)})
            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

        @self.blueprint.route("/products/put/<id>", methods=["PUT"])
        @jwt_required()
        def put(id):
            check_for_admin()
            data = request.get_json()
            if not data:
                return jsonify({"error": "empty request body"}), 400

            name = data.get("name")
            description = data.get("description")
            category_id = data.get("category_id")
            price = data.get("price")
            updated_at = data.get("updated_at")
            if any(not value for value in [name, category_id, price]):
                return jsonify({"error": "missing required arguments"}), 400

            query = "UPDATE products SET "
            update_fields = []
            params = []
            append_update_field(update_fields, params, "name", name)
            append_update_field(update_fields, params, "description", description)
            append_update_field(update_fields, params, "category_id", category_id)
            append_update_field(update_fields, params, "price", price)
            append_update_field(update_fields, params, "updated_at", None)

            query += ", ".join(update_fields) + " WHERE id = %s"
            params.append(id)
            try:
                with connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    if cursor.rowcount > 0:
                        conn.commit()
                        new_data = select_from_table(self.table_name, id=id)
                        return (
                            jsonify({"message": destructuring_utility(new_data)}),
                            200,
                        )
                    else:
                        return (
                            jsonify({"error", "product not found or no changes made"}),
                            404,
                        )
            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

        @self.blueprint.route("/products/patch/<id>", methods=["PATCH"])
        @jwt_required()
        def patch(id):
            check_for_admin()
            data = request.get_json()
            if not data:
                return jsonify({"error": "request body is empty"}), 400
            name = data.get("name")
            description = data.get("description")
            category_id = data.get("category_id")
            price = data.get("price")

            query = f"UPDATE {self.table_name} SET "
            update_fields = []
            params = []
            append_for_patch(update_fields, params, "name", name)
            append_for_patch(update_fields, params, "description", description)
            append_for_patch(update_fields, params, "category_id", category_id)
            append_for_patch(update_fields, params, "price", price)
            append_for_patch(update_fields, params, "updated_at", None)

            query += (", ").join(update_fields) + " WHERE id = %s"
            params.append(id)
            try:
                with connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    if cursor.rowcount > 0:

                        conn.commit()
                        new_data = select_from_table(self.table_name, id=id)
                        return (
                            jsonify({"updated": destructuring_utility(new_data)}),
                            200,
                        )
                    else:
                        return (
                            jsonify({"error": "product could not be updated or found"}),
                            404,
                        )
            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

        @self.blueprint.route("/products/delete/<id>", methods=["DELETE"])
        @jwt_required()
        def delete(id):
            check_for_admin()
            product_to_delete = select_from_table(self.table_name, id=id)
            try:
                result = delete_records_from_table(self.table_name, id=id)
                if result:
                    reset_sequence_id(self.table_name)
                    return (
                        jsonify(
                            {"deleted data": destructuring_utility(product_to_delete)}
                        ),
                        200,
                    )
                else:
                    return jsonify({"error": "could not find or delete product"}), 200
            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

    def register_blueprint(self, app):
        app.register_blueprint(self.blueprint(app))
