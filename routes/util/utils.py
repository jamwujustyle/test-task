import random
import string
from flask import jsonify, abort
from flask_jwt_extended import get_jwt


def destructuring_utility(data):

    if isinstance(data, list):
        result = [dict(row) for row in data]
    elif isinstance(data, dict):
        result = dict(data)
    else:
        result = []
    return jsonify({"msg": result}), 200


def generate_tracking_number(prefix="TRK", length=10):
    characters = string.ascii_uppercase + string.digits

    random_part = "".join(random.choices(characters, k=length))
    tracking_number = f"{prefix}:{random_part}"
    return tracking_number


def append_update_field(fields, params, field_name, value):
    if value is not None:
        fields.append(f"{field_name} = %s")
        params.append(value)
    else:
        fields.append(f"{field_name} = NULL")


def append_for_patch(fields, params, field_name, value):
    if value is not None:
        fields.append(f"{field_name} = %s")
        params.append(value)


def check_for_admin():
    claims = get_jwt()
    if claims.get("role") != "admin":
        abort(401, description="insufficient permissions")
