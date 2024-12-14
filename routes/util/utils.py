import random
import string
from flask import jsonify, abort
from flask_jwt_extended import get_jwt
from db import connect
import re


def destructuring_utility(data):

    if isinstance(data, list):
        result = [dict(row) for row in data]
    elif isinstance(data, dict):
        result = dict(data)
    else:
        result = []
    return result, jsonify({"msg": result}), 200


def generate_tracking_number(prefix="TRK", length=10):
    characters = string.ascii_uppercase + string.digits

    random_part = "".join(random.choices(characters, k=length))
    tracking_number = f"{prefix}:{random_part}"
    return tracking_number


def append_update_field(fields, params, field_name, value):
    if field_name == "updated_at" and value is None:
        fields.append(f"{field_name} = CURRENT_TIMESTAMP")
    elif value is not None:
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
        return jsonify({"error": "insufficient permissions"}), 401


def reset_sequence_id(table_name):
    query = f"""
                    SELECT setval(
                    pg_get_serial_sequence('{table_name}', 'id'),
                    COALESCE((SELECT MIN(id) FROM {table_name}), 1) + 1,
                    false
                    );
                """
    try:
        with connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            if result is not None:
                return (
                    f"serial sequence for {table_name} has been updated to {result[0]}"
                )
            return f"no changes made to serial sequence for {table_name}"
    except Exception as ex:
        abort(400, description=f"error resetting serial sequence: {str(ex)}")


def email_validation(email):
    email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    if not re.match(email_regex, email):
        return jsonify({"error": "invalid email format"}), 400
    return True
