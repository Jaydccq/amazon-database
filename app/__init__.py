from flask import Flask
from flask_login import LoginManager
from .config import Config
from .db import DB
from .reviews import bp as reviews_bp



login = LoginManager()
login.login_view = 'users.login'

@login.user_loader
def load_user(user_id):
    from .models.user import User
    return User.get(user_id)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.db = DB(app)
    login.init_app(app)

    from .index import bp as index_bp
    app.register_blueprint(index_bp)

    from .users import bp as user_bp
    app.register_blueprint(user_bp)
    # adding the reviews blueprint
    from .reviews import bp as reviews_bp
    app.register_blueprint(reviews_bp) 
    ##

    from .seller import bp as seller_bp
    app.register_blueprint(seller_bp)

    return app
