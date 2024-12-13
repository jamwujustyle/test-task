from flask import request, Blueprint, current_app, jsonify, abort
from flask_jwt_extended import get_jwt, jwt_required
from db import connect
from routes.util.utils import check_for_admin
from psycopg2.extras import DictCursor


class CartManagement:
    def __init__(self, app=None):
        self.blueprint = Blueprint("cart_management", __name__)
        self.table_name = "cart"
        if app is not None:
            self.register_blueprint(self.blueprint(app))

        @self.blueprint.route("/cart/post", methods=["POST"])
        @jwt_required()
        def post():
            claims = get_jwt()
            if claims is None:
                abort(401, description="not autorized")
            data = request.get_json()
            if not data:
                return jsonify({"error": "empty request body "}), 400
            quantity = data.get("quantity")
            user_id = data.get("user_id")
            product_id = data.get("product_id")
            if any(not value for value in [user_id, product_id]):
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
                            }
                        ),
                        201,
                    )
            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

        @self.blueprint.route("/cart/get", methods=["GET"])
        @jwt_required()
        def get():
            claims = get_jwt()
            if claims is None:
                return jsonify({"error": "authorization failed"}), 401
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

                    data = [
                        {
                            "user_id": row["user_id"],
                            "product_id": row["product_id"],
                            "quantity": row["quantity"],
                        }
                        for row in result
                    ]
                    return jsonify({"msg": data}), 200
            except Exception as ex:
                return jsonify({"error": str(ex)}), 500

        # @self.blueprint.route("/cart/delete/<id>", methods=["DELETE"])
        # @jwt_required()
        # def delete_by_id():

    def register_blueprint(self, app):
        app.register_blueprint(self.blueprrint(app))
