from heymans.server import create_app
from heymans import config

app = create_app()
if __name__ == '__main__':
    app.run(host=config.flask_host, port=config.flask_port)
