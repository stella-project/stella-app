# Release notes
All notable changes to this project will be documented in this file. 

## Generalize Recommender Endpoints
The stella app differentiates between dataset and publication recommendations. While this was catered to the initial use in the Lilas lab, the goal is to support any type of recommendations. Therefore, the recommender endpoint was simplified so that no specific types are supported. Instead of `recommendations/datasets` and `recommendations/publications` simply the `recommendations` endpoint can now be used. 

Additionally, this helps to maintain the stella-app because the `recommendations` endpoint now also uses the `result_service` like the `ranking` endpoint as well. This means that concurrent requests and custom return formats are also available for recommendations now.

## Make calls to base and experimental systems concurrently
The interleaved ranking is created by combining a ranking from an experimental and a baseline system. These two systems were previously called one after another. Now both systems are called simultaneously which provides some speedups for interleaved rankings.
This applies currently only to the ranking endpoint and not to the recommendation endpoint.

## Remove the Docker Client
The Python Docker Client was used to get the address of experimental systems in docker container so that they can be accessed if the stella-app was run locally outside of the docker network. This was removed and a new local development strategy is introduced. The `docker-compose-dev.yml` uses the `Dockerfile.dev` to build the stella-app and mounts it in the container. This enables hot reloading like and simultaneously the connection through the docker network to the other container.


## Add response passthrough to ranking endpoints
Previously the STELLA infrastructure demanded a fixed response schema for rankings. The ranking systems were expected to return the documents or items in a certain format and the STELLA app would pass the results after the interleaving als in a certain format. This was not flexible and all content needed to be loaded afterwards from external sources based on the returned ID.  

Improving on that, the STELLA App now supports a passthrough mode for the ranking endpoint. This means that the ranking systems can return the documents in any format they like and the STELLA App will return the same format after interleaving. This allows to return the full content of the documents.

To make use of this feature, the experimental systems need additional configurations to tell the STELLA App the JSON Path to the document ranking in the response and the key of the document ID. This can be configured through the `SYSTEMS_CONFIG` environment variable in the docker compose file.

Example:
```
SYSTEMS_CONFIG: |
        {
            "ranker_base": {"type": "ranker", "base": true, "docid": "id", "hits_path": "$.hits.hits"},
            "ranker_exp": {"type": "ranker", "docid": "id", "hits_path": "$.hits.hits"}
        }
```

The results are still saved to the database in the base schema of the STELLA app and the original response will not be saved to the database. This is to ensure fast responses and minimize latency. However therefore a new caching mechanism was needed. Therefore, `Flask-Caching` is used. By default, `FileSystemCache` is used, but this can be changed in the `config.py` file.



## Allow system config as JSON
Allow passing the systems config in the docker compose environment variables as a JSON string. This is cleaner and clearer and will allow the configuration of additional system parameters necessary for future updates.

Before:
```
RECSYS_LIST: gesis_rec_pyterrier gesis_rec_pyserini
RECSYS_BASE: gesis_rec_pyterrier
RANKSYS_LIST: gesis_rank_pyserini_base gesis_rank_pyserini
RANKSYS_BASE: gesis_rank_pyserini_base
```

After:
```
SYSTEMS_CONFIG: |
          [
            {"name": "gesis_rec_pyterrier", "type": "recommender", "base": true},
            {"name": "gesis_rec_pyserini", "type": "recommender"},
            {"name": "gesis_rank_pyserini_base", "type": "ranker", "base": true},
            {"name": "gesis_rank_pyserini", "type": "recommender"}
          ]
```


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


