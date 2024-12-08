from flask import Blueprint, current_app, request, jsonify
from flask_jwt_extended import get_jwt, jwt_required
from db import connect
from psycopg2.extras import DictCursor
from queries.db_queries import select_from_table


class ProductManagement:
    ############### INIT ##############
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
                if not category:
                    return jsonify({"error": "category not found"}), 404
            except Exception as ex:
                current_app.logger.debug("failed to find the category")
            claims = get_jwt()
            if claims.get("role") != "admin":
                current_app.logger.debug("user needs to have role admin")
                return (jsonify({"error": "insufficient permissions"}), 401)
            query = f"""
              INSERT INTO {self.table_name} (name, description, category_id, price)
              VALUES (%s, %s, %s, %s) 
              RETURNING id, name, description, price, category_id;
              """
            # 409
            params = [name, description, category_id, price]
            try:
                with connect() as conn:
                    cursor = conn.cursor(cursor_factory=DictCursor)
                    cursor.execute(query, params)
                    result = cursor.fetchone()
                    if result:
                        current_app.logger.debug(
                            f"successfully inserted into {self.table_name}"
                        )
                        return (
                            jsonify(
                                {
                                    "msg": "inserted data",
                                    "id": result["id"],
                                    "name": name,
                                    "description": description,
                                    "price": price,
                                    "category": (
                                        category["name"]
                                        if category is not None
                                        else None
                                    ),
                                }
                            ),
                            201,
                        )
                    else:
                        return jsonify({"error": "conflict"}), 409

            except Exception as ex:
                current_app.logger.debug("don't know what happened check the response")
                return jsonify({"error": str(ex)}), 500

    def register_blueprint(self, app):
        app.register_blueprint(self.blueprint(app))
