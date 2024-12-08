from db import connect
from flask import Flask
from routes.user import UserManagement
from routes.categories import CategoryManagement
from routes.products import ProductManagement
from flask_mail import Mail
from email_verification.verification import handle_email_verification
from dotenv import load_dotenv
import os
from flask_jwt_extended import JWTManager

load_dotenv()
app = Flask(__name__)

app.config["SECRET_KEY"] = "24e2b6bb0774463e890d1ad7d562c801"
# app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
# app.config["MAIL_PORT"] = os.getenv("MAIL_PORT")
# app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS")
# app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
# app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
# app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")

jwt = JWTManager(app)
mail = Mail(app)


user_management = UserManagement()
category_management = CategoryManagement()
product_management = ProductManagement()
app.register_blueprint(user_management.blueprint)
app.register_blueprint(category_management.blueprint)
app.register_blueprint(product_management.blueprint)
if __name__ == "__main__":
    app.run(debug=True)
