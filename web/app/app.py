import logging
import os
import sys

from app.api import api as api_blueprint
from app.commands import index_systems, init_db_command, seed_db_command
from app.extensions import bootstrap, db, migrate, scheduler
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

    if app.config["DEBUG"] and app.config["SENDFEEDBACK"] and not app.config["TESTING"]:
        print("Initializing and starting scheduler in app factory process")
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
        app.logger.handlers.clear()
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        log_format = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)

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
