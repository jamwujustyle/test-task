from flask import Blueprint, request, current_app, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt
from db import connect
from psycopg2.extras import DictCursor
from queries.db_queries import select_from_table
from routes.util.utils import destructuring_utility, generate_tracking_number


class OrderManagement:
    def __init__(self, app=None):
        self.blueprint = Blueprint("orders-management", __name__)
        self.table_name = "orders"
        if app is not None:
            self.register_blueprint(self.blueprint(app))

        @self.blueprint.route("/orders/post", methods=["POST"])
        @jwt_required()
        def post():
            data = request.get_json()
            if not data:
                return jsonify({"error": "request body is empty"}), 400
            claims = get_jwt()
            if not claims:
                return jsonify({"error": "could not authenticate"}), 401
            user_id = data.get("user_id")
            status = data.get("status")
            shipping_address = data.get("shipping_address")
            payment_method = data.get("payment_method")
            payment_status = data.get("payment_status")
            shipping_status = data.get("shipping_status")
            tracking_number = generate_tracking_number()
            products = data.get("products")
            if any(not value for value in [user_id, shipping_address]):
                return jsonify({"error": "missing required arguments"}), 400

            query = f"""INSERT INTO {self.table_name} 
            (user_id, status, shipping_address, payment_method, payment_status, shipping_status, tracking_number) VALUES (%s, %s, %s, %s, %s, %s, %s ) RETURNING *;"""
            params = [
                user_id,
                status,
                shipping_address,
                payment_method,
                payment_status,
                shipping_status,
                tracking_number,
            ]

            try:
                with connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    order_id = cursor.fetchone()[0]
                    for product in products:
                        product_id = product.get("product_id")
                        quantity = product.get("quantity")
                        price = product.get("price")

                        cursor.execute(
                            """INSERT INTO order_items (order_id, product_id, quantity, price)
                        VALUES (%s, %s, %s, %s) ON CONFLICT (order_id, product_id) DO UPDATE SET quantity = order_items.quantity + 1;""",
                            (order_id, product_id, quantity, price),
                        )
                    conn.commit()
                    return (
                        jsonify(
                            {"msg": "order created successfully", "order_id": order_id}
                        ),
                        201,
                    )
            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

        @self.blueprint.route("/orders/get", methods=["GET"])
        @jwt_required()
        def get_all_orders():
            claims = get_jwt()
            if claims.get("role") != "admin":
                return jsonify({"error": "insufficient permissions"}), 401
            try:
                result = select_from_table(self.table_name)
                return destructuring_utility(result)
            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

        @self.blueprint.route("/orders/get/<id>", methods=["GET"])
        @jwt_required()
        def get_user_by_id(id):
            claims = get_jwt()
            if claims.get("role") != "admin":
                return jsonify({"error": "insufficient permissions"}), 401
            try:
                result = select_from_table(self.table_name, id=id)
                return destructuring_utility(result)
            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

        @self.blueprint.route("/orders/put/<id>", methods=["PUT"])
        @jwt_required()
        def put(id):
            claims = get_jwt()
            if claims.get("role") != "admin":
                return jsonify({"error": "insufficient permissions"}), 401
            data = request.get_json()
            user_id = data.get("user_id")
            order_date = data.get("order_date")
            status = data.get("status")
            shipping_address = data.get("shipping_address")
            billing_address = data.get("billing_address")
            payment_method = data.get("payment_method")
            payment_status = data.get("payment_status")
            shipping_status = data.get("shipping_status")
            tracking_number = data.get("tracking_number")

        @self.blueprint.route("/orders/patch<id>", methods=["PATCH"])
        @jwt_required()
        def patch(id): ...

        @self.blueprint.route("/orders/delete/<id>", methods=["DELETE"])
        @jwt_required()
        def delete(id): ...

    def register_blueprint(self, app):
        app.register_blueprint(self.blueprint(app))
