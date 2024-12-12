from flask import Blueprint, request, current_app, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt
from db import connect
from psycopg2.extras import DictCursor
from queries.db_queries import select_from_table, delete_records_from_table
from routes.util.utils import (
    destructuring_utility,
    generate_tracking_number,
    append_update_field,
    append_for_patch,
    check_for_admin,
)
import json


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

                        cursor.execute(
                            """INSERT INTO order_items (order_id, product_id, quantity)
                        VALUES (%s, %s, %s) ON CONFLICT (order_id, product_id) DO UPDATE SET quantity = order_items.quantity + 1;""",
                            (order_id, product_id, quantity),
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
                query = f"SELECT * FROM {self.table_name}"
                with connect() as conn:
                    cursor = conn.cursor(cursor_factory=DictCursor)
                    cursor.execute(query)
                    orders = cursor.fetchall()
                    # if not orders:
                    #     return jsonify({"error": "no products to fetch"}), 404
                    # return jsonify([dict(order) for order in orders]), 200
                return destructuring_utility(orders)
            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

        @self.blueprint.route("/orders/get/<id>", methods=["GET"])
        @jwt_required()
        def get_order_by_id(id):
            claims = get_jwt()
            if claims.get("role") != "admin":
                return jsonify({"error": "insufficient permissions"}), 401
            try:
                query = f"SELECT * FROM {self.table_name} WHERE id = %s;"
                with connect() as conn:
                    cursor = conn.cursor(cursor_factory=DictCursor)
                    cursor.execute(query, id)
                    orders = cursor.fetchall()
                    if not orders:
                        return jsonify({"error": "no orders to fetch"}), 404

                return destructuring_utility(orders)
            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

        @self.blueprint.route("/orders/put/<id>", methods=["PUT"])
        @jwt_required()
        def put(id):
            claims = get_jwt()
            if claims.get("role") != "admin":
                return jsonify({"error": "insufficient permissions"}), 401
            data = request.get_json()
            if not data:
                return jsonify({"error": "request body is empty"}), 400
            user_id = data.get("user_id")
            status = data.get("status")
            shipping_address = data.get("shipping_address")
            payment_method = data.get("payment_method")
            payment_status = data.get("payment_status")
            shipping_status = data.get("shipping_status")
            tracking_number = data.get("tracking_number")
            products = data.get("products")
            if any(not value for value in [user_id, status, shipping_address]):
                return jsonify({"error": "missing required arguments"}), 400
            query = f"UPDATE {self.table_name} SET "
            update_fields = []
            params = []
            append_update_field(update_fields, params, "user_id", user_id)
            append_update_field(update_fields, params, "status", status)
            append_update_field(
                update_fields, params, "shipping_address", shipping_address
            )

            append_update_field(update_fields, params, "payment_method", payment_method)
            append_update_field(update_fields, params, "payment_status", payment_status)
            append_update_field(
                update_fields, params, "shipping_status", shipping_status
            )
            append_update_field(
                update_fields, params, "tracking_number", tracking_number
            )
            query += ", ".join(update_fields) + " WHERE id = %s RETURNING *;"
            params.append(int(id))
            try:
                with connect() as conn:
                    cursor = conn.cursor(cursor_factory=DictCursor)
                    cursor.execute(query, params)
                    updated = cursor.fetchone()

                    if not updated:
                        return jsonify({"error": "could not update order"}), 400

                    total_price = 0
                    for product in products:
                        product_id = product.get("product_id")
                        quantity = product.get("quantity")
                        cursor.execute(
                            "SELECT price FROM products WHERE id = %s;", (product_id,)
                        )
                        product_price_record = cursor.fetchone()
                        if not product_price_record:
                            return (
                                jsonify({"error": f"product with ID {id} not found"}),
                                404,
                            )
                        product_price = product_price_record["price"]

                        total_price += product_price * quantity
                        order_items_query = f"""
                        INSERT INTO order_items (order_id, product_id, quantity)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (product_id, order_id)
                        DO UPDATE SET quantity = order_items.quantity + %s;                    
                        """
                        cursor.execute(
                            order_items_query,
                            (
                                id,
                                product_id,
                                quantity,
                                quantity,
                            ),
                        )
                    cursor.execute(
                        "UPDATE orders SET total_price = %s WHERE id = %s",
                        (
                            total_price,
                            id,
                        ),
                    )
                    conn.commit()
                    return (
                        jsonify(
                            {"updated order": "updated", "total price": total_price}
                        ),
                        201,
                    )
            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

        @self.blueprint.route("/orders/patch/<id>", methods=["PATCH"])
        @jwt_required()
        def patch(id):
            check_for_admin()
            data = request.get_json()
            if not data:
                return jsonify({"error": "empty request body"}), 400
            user_id = data.get("user_id")
            status = data.get("status")
            shipping_address = data.get("shipping_address")
            payment_method = data.get("payment_method")
            payment_status = data.get("payment_status")
            shipping_status = data.get("shipping_status")
            products = data.get("products")
            update_fields = []
            params = []
            query = f"UPDATE {self.table_name} SET "
            append_for_patch(update_fields, params, "user_id", user_id)
            append_for_patch(update_fields, params, "status", status)
            append_for_patch(
                update_fields, params, "shipping_address", shipping_address
            )
            append_for_patch(update_fields, params, "payment_method", payment_method)
            append_for_patch(update_fields, params, "payment_status", payment_status)
            append_for_patch(update_fields, params, "shipping_status", shipping_status)
            query += ", ".join(update_fields) + " WHERE id = %s RETURNING *;"
            params.append(int(id))
            try:
                with connect() as conn:
                    cursor = conn.cursor(cursor_factory=DictCursor)
                    cursor.execute(query, params)
                    updated = cursor.fetchone()
                    if not updated:
                        return (
                            jsonify({"error": "could not resolve for the first query"}),
                            500,
                        )
                    total_price = 0
                    for product in products:
                        product_id = product["product_id"]
                        quantity = product["quantity"]
                        if any(not value for value in [product_id, quantity]):
                            return jsonify({"error": "invalid data"}), 400

                        cursor.execute(
                            "select price from products where id = %s", (product_id,)
                        )
                        product_price_record = cursor.fetchone()
                        if not product_price_record:
                            return (
                                jsonify(
                                    {
                                        "error": f"could not fetch price for product with id: {product_id}"
                                    }
                                ),
                                404,
                            )
                        product_price = product_price_record["price"]

                        total_price += product_price * quantity
                        order_items_query = f"""
                        INSERT INTO order_items 
                        (order_id, product_id, quantity)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (order_id, product_id)
                        DO UPDATE SET quantity = order_items.quantity + %s;
                        """
                        cursor.execute(
                            order_items_query, (id, product_id, quantity, quantity)
                        )
                    cursor.execute(
                        f"UPDATE orders SET total_price = %s WHERE id = %s",
                        (total_price, id),
                    )
                    conn.commit()
                    return jsonify({"msg": "updated successfully"}), 200

            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

        @self.blueprint.route("/orders/delete/<id>", methods=["DELETE"])
        @jwt_required()
        def delete(id):
            check_for_admin()
            data_to_delete = select_from_table(self.table_name, id=id)
            try:
                result = delete_records_from_table(self.table_name, id=id)
                if result is not None:
                    reset_id_sequence()
                    return jsonify({"deleted data": data_to_delete}), 200
            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

        def reset_id_sequence():
            query = f"""
                SELECT setval(
                            pg_get_serial_sequence('{self.table_name}', 'id'),
                            COALESCE((SELECT MIN(id) FROM {self.table_name}), 1),
                            false
                            );
                """
            try:
                with connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query)
                    conn.commit()
                    return "sequence reset successfully"
            except Exception as ex:
                current_app.logger.debug(f"error resetting id sequence {str(ex)}")
                return None

    def register_blueprint(self, app):
        app.register_blueprint(self.blueprint(app))
