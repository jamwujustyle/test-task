from db import connect
from flask import Flask
import logging
from router.register import UserManagement

logging.basicConfig(
    level=logging.DEBUG,
    format="  %(name)s - %(levelname)s - %(message)s",
    # logging.debug
    # logging.info
    # logging.warning
    # logging.error
    # logging.critical
)


app = Flask(__name__)
user_management = UserManagement()
app.register_blueprint(user_management.blueprint)
if __name__ == "__main__":
    app.run(debug=True)
