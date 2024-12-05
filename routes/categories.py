from flask import Blueprint, jsonify, request, current_app
from db import connect
from flask_jwt_extended import create_access_token, jwt_required, get_jwt
from psycopg2.extras import DictCursor
from queries.db_queries import select_from_table, insert_into_users


class CategoryManagement:
    ###########################INIT ROUTING################################
    def __init__(self, app=None):
        self.blueprint = Blueprint("categories-management", __name__)
        if app is not None:
            self.register_blueprint(app)

        @self.blueprint.route("/categories/post", methods=["POST"])
        @jwt_required()
        def post():
            data = request.get_json()
            if not data:
                return jsonify({"error": "invalid request"}), 400
            return jsonify({"data: ": data}), 201

    def register_blueprint(self, app):
        app.register_blueprint(self.blueprint)
