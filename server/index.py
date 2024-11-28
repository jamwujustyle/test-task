from db import connect
from flask import Flask

from router.register import UserManagement

app = Flask(__name__)

if __name__ == "__main__":
    app.run(debug=True)
