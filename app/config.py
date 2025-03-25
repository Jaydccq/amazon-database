import os
from urllib.parse import quote_plus


class Config(object):
    # SECRET_KEY = os.environ.get('SECRET_KEY')
    SECRET_KEY = 'gingerbread-miniamazon-secret-key'
    SQLALCHEMY_DATABASE_URI = 'postgresql://{}:{}@{}:{}/{}'\
        .format(os.environ.get('DB_USER'),
                quote_plus(os.environ.get('DB_PASSWORD')),
                os.environ.get('DB_HOST'),
                os.environ.get('DB_PORT'),
                os.environ.get('DB_NAME'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
