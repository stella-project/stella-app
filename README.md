# STELLA Application

## Setup

#### Independent of `stella-server`
1. Build the `stella-app` with Docker: `docker-compose -f local.yml up -d`


#### With [`stella-server`](https://github.com/stella-project/stella-server)
1. Set up the `stella-server` first. It will provide the shared Docker network.
2. Build the `stella-app` with Docker: `docker-compose up -d`

## Citation

We provide citation information via the [CITATION file](./CITATION.cff). If you use `stella-app` in your work, please cite our repository as follows:

> Schaer P, Schaible J, Garcia Castro LJ, Breuer T, Tavakolpoursaleh N, Wolff B. STELLA Search. Available at https://github.com/stella-project/stella-app/

We recommend you include the retrieval date.

## License

`stella-app` is licensed under the [GNU GPLv3 license](https://github.com/stella-project/stella-app/blob/master/LICENSE). If you modify `stella-app` in any way, please link back to this repository.
