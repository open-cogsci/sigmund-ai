from heymans.server import create_app
from heymans import config

if __name__ == '__main__':
    app = create_app()
    app.run(host=config.flask_host, port=config.flask_port)
