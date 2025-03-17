from aiocache import Cache
from aiocache.serializers import JsonSerializer
from flask_apscheduler import APScheduler
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


class FlaskAsyncCache:
    """Flask extension to manage async caching."""

    def init_app(self, app):
        app.cache = Cache(Cache.MEMORY, serializer=JsonSerializer())
        return app


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bootstrap = Bootstrap()
scheduler = APScheduler()
cache = FlaskAsyncCache()
