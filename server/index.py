from flask import Flask
from db import connect

app = Flask(__name__)

connect()


if __name__ == "__main__":
    app.run(debug=True)
