from flask_swagger_ui import get_swaggerui_blueprint


def setup_swagger(app):
    swagger_url = "/swagger"
    api_url = "/static/swagger.json"

    swaggerui_blueprint = get_swaggerui_blueprint(
        swagger_url, api_url, config={"app_name": "test_task"}
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=swagger_url)
