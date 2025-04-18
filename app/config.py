import os
from urllib.parse import quote_plus


class Config(object):
    SECRET_KEY = 'gingerbread-miniamazon-secret-key'

    password = os.environ.get('DB_PASSWORD', '')
    password_encoded = quote_plus(password.encode('utf-8'))

    SQLALCHEMY_DATABASE_URI = 'postgresql://{}:{}@{}:{}/{}'.format(
        os.environ.get('DB_USER', ''),
        password_encoded,
        os.environ.get('DB_HOST', 'localhost'),
        os.environ.get('DB_PORT', '5432'),
        os.environ.get('DB_NAME', '')
    )

    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static/uploads')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
