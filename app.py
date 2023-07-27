from heymans.server import app
from heymans import config

if __name__ == '__main__':
    app.run(host=config.flask_host, port=config.flask_port)
