from flask import Flask
from server.router.users_management.register import blueprint

app = Flask(__name__)
