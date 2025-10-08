# STELLA Application
[![CI status](https://img.shields.io/github/actions/workflow/status/stella-project/stella-app/push.yml?branch=main&style=flat-square)](https://github.com/stella-project/stella-app/actions/workflows/push.yml)
[![Issues](https://img.shields.io/github/issues/stella-project/stella-app?style=flat-square)](https://github.com/stella-project/stella-app/issues)
[![Pull requests](https://img.shields.io/github/issues-pr/stella-project/stella-app?style=flat-square)](https://github.com/stella-project/stella-app/pulls)
[![Commit activity](https://img.shields.io/github/commit-activity/m/stella-project/stella-app?style=flat-square)](https://github.com/stella-project/stella-app/commits)
[![Maintenance](https://img.shields.io/maintenance/yes/2025?style=flat-square)](https://github.com/stella-project/stella-app/graphs/contributors)
[![License](https://img.shields.io/github/license/stella-project/stella-app?style=flat-square)](LICENSE)
[![Coverage](https://img.shields.io/endpoint?url=https://stella-project.org/stella-app/coverage-badge.json&style=flat-square)](https://stella-project.org/stella-app/coverage-badge.svg)

The `stella-app` will be deployed at sites that want to conduct IR and recommender experiments and have them evaluated with real-world user interactions. The `stella-app` is a multi-container application composed of several experimental micro-services that are built with the [`stella-micro-template`](https://github.com/stella-project/stella-micro-template). It provides experimental rankings and recommendations and receives feedback data that will be posted to the central [`stella-server`](https://github.com/stella-project/stella-server).

## Setup
#### Local development
1. Build `docker compose -f docker-compose-dev.yml build --no-cache`
2. Run `docker compose -f docker-compose-dev.yml up -d`

#### With [`stella-server`](https://github.com/stella-project/stella-server)
1. Set up the `stella-server` first. It will provide the shared Docker network.
2. Build the `stella-app` with Docker: `docker compose up -d`

**A setup guide for the entire infrastructure can be found [here](https://github.com/stella-project/stella-server/blob/master/doc/README.md).**

## Citation

We provide citation information via the [CITATION file](./CITATION.cff). If you use `stella-app` in your work, please cite our repository as follows:

> Schaer P, Schaible J, Garcia Castro LJ, Breuer T, Tavakolpoursaleh N, Wolff B. STELLA Search. Available at https://github.com/stella-project/stella-app/

We recommend you include the retrieval date.

## License

`stella-app` is licensed under the [GNU GPLv3 license](https://github.com/stella-project/stella-app/blob/master/LICENSE). If you modify `stella-app` in any way, please link back to this repository.
