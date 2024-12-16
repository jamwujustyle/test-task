from flask import request, Blueprint, current_app, jsonify, abort
from flask_jwt_extended import get_jwt, jwt_required, get_jwt_identity, current_user
from db import connect
from routes.util.utils import destructuring_utility, reset_sequence_id
from psycopg2.extras import DictCursor
from queries.db_queries import select_from_table, delete_records_from_table
from routes.util.utils import check_for_admin


class CartManagement:
    def __init__(self, app=None):
        self.blueprint = Blueprint("cart_management", __name__)
        self.table_name = "cart"
        if app is not None:
            self.register_blueprint(self.blueprint(app))

        @self.blueprint.route("/cart/post", methods=["POST"])
        @jwt_required()
        def post():
            data = request.get_json()
            if not data:
                return jsonify({"error": "empty request body "}), 400
            quantity = data.get("quantity")
            user_id = data.get("user_id")
            product_id = data.get("product_id")
            if any(not value for value in [user_id, product_id, quantity]):
                return jsonify({"error": "missing required arguments"}), 400

            params = [user_id, product_id, quantity, quantity]

            try:
                query = f"""INSERT INTO {self.table_name}
                  (user_id, product_id, quantity) VALUES (%s, %s, %s)
                  ON CONFLICT (user_id, product_id) DO UPDATE
                  SET quantity = cart.quantity + %s RETURNING *;
                  """
                with connect() as conn:
                    cursor = conn.cursor(cursor_factory=DictCursor)
                    cursor.execute(query, params)
                    result = cursor.fetchone()
                    if result is None:
                        return jsonify({"error": "could not fetch, cursor error"}), 400
                    conn.commit()
                    return (
                        jsonify(
                            {
                                "msg": f"inserted data into table {self.table_name}",
                                "user_id": result["user_id"],
                                "product_id": result["product_id"],
                                "quantity": result["quantity"],
                                "id": result["id"],
                            }
                        ),
                        201,
                    )
            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

        @self.blueprint.route("/cart/get", methods=["GET"])
        @jwt_required()
        def get():
            try:
                query = f"SELECT * FROM {self.table_name};"
                with connect() as conn:
                    cursor = conn.cursor(cursor_factory=DictCursor)
                    cursor.execute(query)
                    result = cursor.fetchall()

                    if result is None:
                        return (
                            jsonify(
                                {
                                    "error": f"could not fetch from table {self.table_name}"
                                }
                            ),
                            500,
                        )
                    return jsonify({"msg": destructuring_utility(result)}), 200
            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

        @self.blueprint.route("/cart/delete/<id>", methods=["DELETE"])
        @jwt_required()
        def delete_by_id(id):
            if check_for_admin() is None:
                return jsonify({"error": "insufficient permissions"}), 401
            try:
                data_to_delete = select_from_table(self.table_name, id=id)
                if data_to_delete is None:
                    return jsonify({"error": f"no record found with id {id}"}), 404
                destructured_data = destructuring_utility(data_to_delete)

                result = delete_records_from_table(self.table_name, id=id)
                if result is None:
                    return jsonify({"error": "deletion failed"}), 400
                reset_sequence_id(self.table_name)
                return jsonify({"deleted data": destructured_data}), 200
            except ValueError as ve:
                return jsonify({"value error": str(ve)}), 500
            except Exception as ex:
                return jsonify({"unexpected error": str(ex)}), 500

        @self.blueprint.route("/cart/delete/user/<id>", methods=["DELETE"])
        @jwt_required()
        def delete_for_user(id):
            identity = get_jwt_identity()
            try:
                with connect() as conn:
                    with conn.cursor(cursor_factory=DictCursor) as cursor:
                        user = select_from_table("users", email=identity)
                        if not user:
                            return (
                                jsonify({"error": "user at the given id not found"}),
                                404,
                            )
                        if not user:
                            return jsonify({"error": "user not found"}), 404
                        cursor.execute(
                            f"SELECT * FROM {self.table_name} WHERE user_id = %s;",
                            (id,),
                        )
                        cart = cursor.fetchall()
                        if not cart:
                            return jsonify({"error": "cart not found"}), 404

                        if user.get("role") == "admin" or cart[0][1] == user.get("id"):
                            cursor.execute(
                                f"DELETE FROM {self.table_name} WHERE user_id = %s;",
                                (id,),
                            )
                            conn.commit()
                            return (
                                jsonify({"msg": "user's cart deleted successfully"}),
                                200,
                            )
                        elif user.get("id") != cart[1]:
                            return jsonify({"error": "cart must belong to user"}), 401
                        else:
                            return jsonify({"error": "insufficient permissions"}), 401
            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

    def register_blueprint(self, app):
        app.register_blueprint(self.blueprrint(app))
