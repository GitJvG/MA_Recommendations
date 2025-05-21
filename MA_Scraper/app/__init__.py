import threading
from flask import Flask, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from MA_Scraper.Env import load_config, Env
from sqlalchemy import inspect
from user_agents import parse
from MA_Scraper.app.CacheManager import CacheManager

backend = Env.get_instance().ytbackend
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cache_manager = CacheManager()
if backend == 'YTAPI':
    from MA_Scraper.app.API import YouTubeClient
    youtube_client = YouTubeClient()
else: 
    youtube_client = False
run_once_lock = threading.Lock()
if backend == 'YTM':
    import MA_Scraper.YTMAPI.ytmusicapi as ytmusic
    ytm = ytmusic.YTMusic('browser.json')
else:
    ytm = None

def get_device():
    if not hasattr(g, "device") or not hasattr(g, "items"):
        user_agent = request.headers.get("User-Agent", "")
        parsed_ua = parse(user_agent)
        if parsed_ua.is_mobile:
            g.device = "mobile"
            g.items = 3
        else:
            g.device = "desktop"
            g.items = 6

def create_app(test_config=None):
    app = Flask(__name__)

    # Load the config
    app.config['SECRET_KEY'] = load_config('Secret_Key')
    app.config['SQLALCHEMY_DATABASE_URI'] = load_config('SQL_Url')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['YT_API_KEY'] = load_config('yt_api_key')
    if youtube_client: 
        youtube_client.init_app(app.config['YT_API_KEY'])

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @app.before_request
    def create_database():
        with run_once_lock:
            inspector = inspect(db.engine)
            if not inspector.has_table('user'): 
                db.create_all()
                print("Database tables created.")
    
    @app.before_request
    def init_device():
        get_device()

    with app.app_context():
        from MA_Scraper.app.models import User, Band, Similar_band, Discography, Users, Member, BandGenres, BandHgenres, BandPrefixes, Prefix, Theme, Themes, Candidates, Band_logo

        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))

    from MA_Scraper.app.routes import main as main
    app.register_blueprint(main)

    from MA_Scraper.app.auth import auth as auth
    app.register_blueprint(auth)

    from MA_Scraper.app.extension import extension as extension
    app.register_blueprint(extension)

    return app