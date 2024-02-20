# Release notes
All notable changes to this project will be documented in this file.

## Update to Python 3.9 and Flask 3.0
- Update minimal Python version to 3.9
    - Update the `python` version in the `Dockerfile` to `3.9`
    - Canfigure automatic tests in github actions to run on `>3.9`
    
- Rework project structure to use a factory pattern
    - Create a `web` directory for the flask app
    - Move Docker compose files to the Docker directory

- Move database seeding to a flask command
    - Create the `seed-db` command
    - remove the seeding from the `__init__.py` file

- Restructure Config file

- Move `core` to `services`
    - Move `index.py` to `services` directory
    - Move `cron` to `cron_services`
    - Move `interleve` to `interleave_services`

- Cleanup
    - Remove old docker compose files

- Switch to new FlaskSQLAlchemy query API
    - Use `db.session.query(<Object>)` instead of `<Object>.query`

- Add database migration support
    - Add `flask-migrate` to the requirements
    - Add `migrate` command to the `entrypoint.sh`

- Rework the command to run the app in the docker compose file
    - Use `flask run` instead of `python stella_app.py`
    - Use `flask seed-db` to initially setup the database.

- Add an `entrypoint.sh` to handle the database setup and running the app
    - Add `entrypoint.sh` to the `stella-app` Dockerfile
    - Update the startup command in the docker compose file

- Add a `wait-for-it.sh` script to wait for the database to be ready before the server initializes the database
    - Add `wait-for-it.sh`
    - Update the entrypoint to use `wait-for-it.sh`


