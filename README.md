# STELLA application

## Prototype
This repository contains a first prototype of the STELLA application which will be deployed at the sites.
The API can be used to send a request to a (minimal) flask application. In return, the flask app will send back a
ranking which is retrieved from a container running Solr.

### Setup - Linux

1. Install [Docker](https://docs.docker.com/v17.12/install/)
2. Install [docker-compose](https://docs.docker.com/compose/install/)
3. [Add user to Docker group](https://docs.docker.com/install/linux/linux-postinstall/)
4. Make sure `docker.sock` is accessible (`/var/run/docker.sock` &rarr; `docker-compose.yml`)
5. Set path to sample data which will be indexed by Solr-container (&rarr; `docker-compose.yml`)
6. Copy some sample data to `~/data/sample`
7. Run `docker-compose up`. Depending on the size of the sample data collection, you have to wait before sending the first request to the API in order to retrieve results.

### Setup - MacOS

0. Install [Homebrew](https://brew.sh)
1. Install Docker:`brew cask install docker` 
2. Install Docker-compose:`brew cask install docker-compose` 
3. Copy some sample data to `~/data/sample`
4. Run `docker-compose up`. Depending on the size of the sample data collection, you have to wait before sending the first request to the API in order to retrieve results.

### Endpoints

- `GET /`: See a list of available containers that are running.

- `GET /stella/api/site/test/<string:container_name>`: Run test script in container whose name is specified by the endpoint (currently only `solr-container` is supported).

- `GET /stella/api/site/ranking/<string:query>`: Retrieve a ranking corresponding to the query specified at the endpoint. A JSON object with maximally 10 entries will be returned.

### To do

- [ ] output format of search script
- [ ] initial indexing of all containers, when starting the application
- [x] additional (prototypical) search engine, e.g. elasticsearch, and scheduling between search engines
- [x] Solr to external repository
- [ ] DB/storage containing meta-info about docker-containers
- [ ] Webhook in repos of experimental systems: PING stella-server
