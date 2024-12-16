import random
import string
from flask import jsonify, abort
from flask_jwt_extended import get_jwt
from db import connect
import re
from psycopg2.extras import DictCursor


def destructuring_utility(data):

    if isinstance(data, list):
        result = [dict(row) for row in data]
    elif isinstance(data, dict):
        result = dict(data)
    else:
        result = []
    return result


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
    elif field_name == "updated_at" and value is None:
        fields.append(f"{field_name} = CURRENT_TIMESTAMP")


def check_for_admin():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return None
    return True


def reset_sequence_id(table_name):
    if table_name == "order_items":
        query = f"""
                    SELECT setval(
                    pg_get_serial_sequence('{table_name}', 'order_id'),
                    COALESCE((SELECT MAX(order_id) FROM {table_name}), 1) + 1,
                    false
                    );
                """
    else:
        query = f"""
                        SELECT setval(
                        pg_get_serial_sequence('{table_name}', 'id'),
                        COALESCE((SELECT MAX(id) FROM {table_name}), 1) + 1,
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


def handle_tracking_number(table_name, id, tracking_number):
    with connect() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(
                f"SELECT tracking_number FROM {table_name} WHERE id = %s;", (id,)
            )
            existing_record = cursor.fetchone()
            if existing_record and existing_record == "tracking_number":
                tracking_number = None
