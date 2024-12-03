from db import connect
from flask import Flask
from user import UserManagement
from flask_mail import Mail
from verification import handle_email_verification
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)

app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
app.config["MAIL_PORT"] = os.getenv("MAIL_PORT")
app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS")
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")

mail = Mail(app)

user_management = UserManagement()
app.register_blueprint(user_management.blueprint)
if __name__ == "__main__":
    app.run(debug=True)
