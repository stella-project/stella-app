# STELLA Application

The `stella-app` will be deployed at sites that want to conduct IR and recommender experiments and have them evaluated with real-world user interactions. The `stella-app` is a multi-container application composed of several experimental micro-services that are built with the [`stella-micro-template`](https://github.com/stella-project/stella-micro-template). It provides experimental rankings and recommendations and receives feedback data that will we posted to the central [`stella-server`](https://github.com/stella-project/stella-server).

## Setup

#### Independent of `stella-server`
1. Build the `stella-app` with Docker: `docker-compose -f local.yml up -d`


#### With [`stella-server`](https://github.com/stella-project/stella-server)
1. Set up the `stella-server` first. It will provide the shared Docker network.
2. Build the `stella-app` with Docker: `docker-compose up -d`

**A setup guide for the entire infrastructure can be found [here](https://github.com/stella-project/stella-server/blob/master/doc/README.md).**

## Citation

We provide citation information via the [CITATION file](./CITATION.cff). If you use `stella-app` in your work, please cite our repository as follows:

> Schaer P, Schaible J, Garcia Castro LJ, Breuer T, Tavakolpoursaleh N, Wolff B. STELLA Search. Available at https://github.com/stella-project/stella-app/

We recommend you include the retrieval date.

## License

`stella-app` is licensed under the [GNU GPLv3 license](https://github.com/stella-project/stella-app/blob/master/LICENSE). If you modify `stella-app` in any way, please link back to this repository.
