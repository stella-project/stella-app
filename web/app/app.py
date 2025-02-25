import logging
import os
import sys

from app.api import api as api_blueprint
from app.commands import index_systems, init_db_command, seed_db_command
from app.extensions import bootstrap, cache, db, migrate, scheduler
from app.main import main as main_blueprint
from config import config
from flask import Flask


def create_app(config_name=None):
    """Create application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object or dictionary to use.
    """
    config_name_environment = os.getenv("FLASK_CONFIG", "test")
    app = Flask(__name__.split(".")[0])

    # Load the default configuration
    app.config.from_object(config[config_name_environment])

    # If a test config or other config object is provided, load it
    if config_name:
        if isinstance(config_name, dict):
            app.config.update(config_name)
        else:
            app.config.from_object(config[config_name])

    if app.config["DEBUG"] and not app.config["TESTING"]:
        print("Initializing and starting scheduler inside Gunicorn master process")
        scheduler.init_app(app)
        scheduler.start()
        print("Scheduler started in app factory process")

    configure_logger(app)
    register_extensions(app)
    register_blueprints(app)
    register_commands(app)
    return app


def configure_logger(app):
    """Configure loggers."""
    if app.config["DEBUG"]:
        log_format = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"

        logging.basicConfig(level=logging.DEBUG, format=log_format)

        # StreamHandler for logging to console
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter(log_format))

        if not any(isinstance(h, logging.StreamHandler) for h in app.logger.handlers):
            app.logger.addHandler(stream_handler)

        # FileHandler for logging to a file
        # file_handler = logging.FileHandler(
        #     "data/log/stella-app.log"
        # )  # Define your log file name
        # file_handler.setFormatter(logging.Formatter(log_format))
        # if not any(isinstance(h, logging.FileHandler) for h in app.logger.handlers):
        #     app.logger.addHandler(file_handler)

        app.logger.info("Logging setup for debug complete.")

    else:
        del app.logger.handlers[:]
        gunicorn_logger = logging.getLogger("gunicorn.error")
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

        app.logger.info("Logging setup complete.")


def register_extensions(app):
    """Register Flask extensions."""
    db.init_app(app)
    migrate.init_app(app, db)
    bootstrap.init_app(app)
    cache.init_app(app)
    return app


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(main_blueprint)
    app.register_blueprint(api_blueprint, url_prefix="/stella/api/v1")
    return None


def register_commands(app):
    """Register Click commands."""
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_db_command)
    app.cli.add_command(index_systems)
