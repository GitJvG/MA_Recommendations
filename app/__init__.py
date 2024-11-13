import threading
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from Env import load_config
from sqlalchemy import inspect

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

# Lock for ensuring the database is created only once
run_once_lock = threading.Lock()

def create_app(test_config=None):
    app = Flask(__name__)

    # Load the config
    app.config['SECRET_KEY'] = load_config('Secret_Key')  # Adjust to your config method
    app.config['SQLALCHEMY_DATABASE_URI'] = load_config('SQL_Url')  # Adjust to your config method
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions with the app instance
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Updated to use the auth blueprint

    # Ensure the database is created only once
    @app.before_request
    def create_database():
        with run_once_lock:
            inspector = inspect(db.engine)
            if not inspector.has_table('users'): 
                db.create_all()
                print("Database tables created.")

    # Import models here to avoid circular imports
    with app.app_context():
        from .models import users, DIM_Band, DIM_Similar_Band, DIM_Discography, DIM_Details, UserBandPreference, DIM_Member, DIM_Genre, DIM_Prefix, Bandgenre

        # User Loader function for Flask-Login
        @login_manager.user_loader
        def load_user(user_id):
            return users.query.get(int(user_id))

    # Import routes
    from .routes import main as main
    app.register_blueprint(main)

    # Import auth routes
    from .auth import auth as auth  # Make sure your auth blueprint is correctly imported
    app.register_blueprint(auth)

    return app
