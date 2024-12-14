from db import connect
from flask import Flask
from routes.users import UserManagement
from routes.categories import CategoryManagement
from routes.products import ProductManagement
from routes.orders import OrderManagement
from routes.cart import CartManagement
from flask_mail import Mail
from email_verification.verification import handle_email_verification
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
from swagger.swagger import setup_swagger
from flask_cors import CORS

load_dotenv()
app = Flask(__name__)
CORS(app)

app.config["SECRET_KEY"] = "d7d562c801"

jwt = JWTManager(app)
setup_swagger(app)
mail = Mail(app)


user_management = UserManagement()
category_management = CategoryManagement()
product_management = ProductManagement()
order_management = OrderManagement()
cart_management = CartManagement()
app.register_blueprint(user_management.blueprint)
app.register_blueprint(category_management.blueprint)
app.register_blueprint(product_management.blueprint)
app.register_blueprint(order_management.blueprint)
app.register_blueprint(cart_management.blueprint)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
