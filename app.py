from sigmund.server import create_app
from sigmund import config

app = create_app()
if __name__ == '__main__':
    app.run(host=config.flask_host, port=config.flask_port)
    # app.run(host=config.flask_host, port=config.flask_port, ssl_context="adhoc", debug=True)
