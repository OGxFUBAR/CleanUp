from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)

    # Secret key for session management
    app.config['SECRET_KEY'] = 'your-secret-key'  # Replace with a secure key

    # Configure the SQLite database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize Flask extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Specify the login view for unauthorized users
    login_manager.login_view = 'main.login'

    # Register the blueprint for routes
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app
