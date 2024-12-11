import random
import string
from flask import jsonify


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
