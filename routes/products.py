from flask import Blueprint, current_app, request, jsonify
from flask_jwt_extended import get_jwt, jwt_required
from db import connect
from psycopg2.extras import DictCursor
from queries.db_queries import select_from_table, delete_records_from_table


class ProductManagement:
    def __init__(self, app=None):
        self.blueprint = Blueprint("product_management", __name__)
        self.table_name = "products"
        if app is not None:
            self.register_blueprint(self.blueprint(app))

        @self.blueprint.route("/products/post", methods=["POST"])
        @jwt_required()
        def post():
            data = request.get_json()
            if not data:
                current_app.logger.debug("request body is empty")
                return jsonify({"error": "missinq required arguments"}), 400
            claims = get_jwt()
            if claims.get("role") != "admin":
                return jsonify({"error": "insufficient permissions"}), 401
            name = data.get("name")
            description = data.get("description")
            category_id = data.get("category_id")
            price = data.get("price")
            if not name or not category_id or not price:
                current_app.logger.debug(
                    "request body lacks arguments (name, price, parent_id)"
                )
                return jsonify({"error": "missing required arguments"}), 400

            try:
                category_id = int(category_id) if category_id is not None else None
            except ValueError as ex:
                current_app.logger.debug("error converting category_id to integer")
                return jsonify({"error": str(ex)}), 409

            try:
                category = select_from_table("categories", id=category_id)
                if category is None:
                    return jsonify({"error": "cant get category"})
                current_app.logger.debug(f"here is your category: {category}")
            except Exception as ex:
                return jsonify({"error": str(ex)}), 404
            query = f"""INSERT INTO {self.table_name} (name, description, category_id, price) VALUES (%s, %s, %s, %s) RETURNING name, description, category_id, price;"""
            params = [name, description, category_id, price]
            try:
                with connect() as conn:
                    cursor = conn.cursor(cursor_factory=DictCursor)
                    cursor.execute(query, params)
                    result = cursor.fetchone()
                    if result is None:
                        return jsonify({"error": "found nothing"}), 404
                    conn.commit()
                    return (
                        jsonify(
                            {
                                "msg": "entry successfull",
                                "parent category": category["name"],
                                "name": name,
                                "description": description,
                                "price": price,
                                "category id": category_id,
                            }
                        ),
                        201,
                    )
            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

        @self.blueprint.route("/products/get", methods=["GET"])
        def get_all_products():
            query = f"""SELECT * FROM {self.table_name};"""
            try:
                with connect() as conn:
                    cursor = conn.cursor(cursor_factory=DictCursor)
                    cursor.execute(query)
                    products = cursor.fetchall()
                    if products is not None:

                        result = [
                            {
                                "id": product["id"],
                                "name": product["name"],
                                "description": product["description"],
                                "price": product["price"],
                                "created at": product["created_at"],
                                "updated at": product["updated_at"],
                                "category id": product["category_id"],
                            }
                            for product in products
                        ]
                        return jsonify(result)
                    else:
                        return jsonify({"error": "no products found"}), 404

            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

        @self.blueprint.route("/products/get/<id>", methods=["GET"])
        def get_by_id(id):
            try:
                product = select_from_table(self.table_name, id=id)
                if product is not None:
                    return jsonify(
                        {
                            "id": product["id"],
                            "name": product["name"],
                            "description": product["description"],
                            "price": product["price"],
                            "created at": product["created_at"],
                            "updated at": product["updated_at"],
                            "category id": product["category_id"],
                        }
                    )
                else:
                    return jsonify({"error": "product not found"}), 404

            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

        @self.blueprint.route("/products/put/<id>", methods=["PUT"])
        @jwt_required()
        def put(id):
            data = request.get_json()
            if not data:
                return jsonify({"error": "empty request body"}), 400
            claims = get_jwt()
            if claims.get("role") != "admin":
                return jsonify({"error": "insufficient permissions"}), 401
            name = data.get("name")
            description = data.get("description")
            category_id = data.get("category_id")
            price = data.get("price")
            updated_at = data.get("updated_at")
            if not name or not price or not category_id:
                return jsonify({"error": "missing required arguments"}), 400

            query = "UPDATE products SET "
            update_fields = []
            params = []
            if name:
                update_fields.append("name = %s")
                params.append(name)
            if description is not None:
                update_fields.append("description = %s")
                params.append(description)
            else:
                update_fields.append("description = NULL")
            if category_id:
                update_fields.append("category_id = %s")
                params.append(category_id)
            if price:
                update_fields.append("price = %s")
                params.append(price)
            if updated_at is not None:
                update_fields.append("updated_at = %s")
                params.append(updated_at)
            else:
                update_fields.append("updated_at = CURRENT_TIMESTAMP")

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
                            jsonify(
                                {
                                    "message": "product updated successfully",
                                    "new data": new_data,
                                }
                            ),
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
            claims = get_jwt()
            if claims.get("role") != "admin":
                return jsonify({"error": "insufficient permissions"}), 401

            data = request.get_json()
            if not data:
                return jsonify({"error": "request body is empty"}), 400
            name = data.get("name")
            description = data.get("description")
            category_id = data.get("category_id")
            updated_at = data.get("updated_at")
            price = data.get("price")

            query = f"UPDATE {self.table_name} SET "
            update_fields = []
            params = []

            if name:
                update_fields.append("name = %s")
                params.append(name)
            if description:
                update_fields.append("description = %s")
                params.append(description)
            if category_id:
                update_fields.append("category_id = %s")
                params.append(category_id)
            if updated_at is not None:
                update_fields.append("updated_at = %s")
                params.append(updated_at)
            else:
                updated_at.append("updated_at = NULL")
            if price:
                update_fields.append("price = %s")
                params.append(price)
            query += (", ").join(update_fields) + " WHERE id = %s"
            params.append(id)
            try:
                with connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    if cursor.rowcount > 0:

                        conn.commit()
                        return (
                            jsonify(
                                {
                                    "msg": "product updated successfully",
                                    "name": name,
                                    "description": description,
                                    "category id": category_id,
                                    "price": price,
                                    "updated at": updated_at,
                                }
                            ),
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
            claims = get_jwt()
            if claims.get("role") != "admin":
                return jsonify({"error": "insufficient permissions"}), 401
            product_to_delete = select_from_table(self.table_name, id=id)
            try:
                result = delete_records_from_table(self.table_name, id=id)
                if result is not None:
                    reset_id_sequence()
                    return jsonify({"deleted data": product_to_delete}), 200
                else:
                    return jsonify({"error": "could not find or delete product"}), 200
            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

        def reset_id_sequence():
            query = f"""
                SELECT setval(
                            pg_get_serial_sequence('{self.table_name}', 'id'),
                            (SELECT MIN(id) FROM {self.table_name}),
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

    def register_blueprint(self, app):
        app.register_blueprint(self.blueprint(app))
