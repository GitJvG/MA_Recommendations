import threading
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from Env import load_config
from sqlalchemy import inspect
from .API import YouTubeClient
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
youtube_client = YouTubeClient()
run_once_lock = threading.Lock()

def create_app(test_config=None):
    app = Flask(__name__)

    # Load the config
    app.config['SECRET_KEY'] = load_config('Secret_Key')
    app.config['SQLALCHEMY_DATABASE_URI'] = load_config('SQL_Url')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['YT_API_KEY'] = load_config('yt_api_key')

    # Initialize extensions with the app instance
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Updated to use the auth blueprint
    youtube_client.init_app(app.config['YT_API_KEY'])
    
    # Ensure the database is created only once
    @app.before_request
    def create_database():
        with run_once_lock:
            inspector = inspect(db.engine)
            if not inspector.has_table('user'): 
                db.create_all()
                print("Database tables created.")

    # Import models here to avoid circular imports
    with app.app_context():
        from .models import user, band, similar_band, discography, details, users, member, genre, prefix, genres, theme, themes, candidates

        # User Loader function for Flask-Login
        @login_manager.user_loader
        def load_user(user_id):
            return user.query.get(int(user_id))

    # Import routes
    from .routes import main as main
    app.register_blueprint(main)

    # Import auth routes
    from .auth import auth as auth
    app.register_blueprint(auth)

    from .extension import extension as extension
    app.register_blueprint(extension)

    return app
