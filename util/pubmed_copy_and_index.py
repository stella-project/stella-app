import docker


if __name__ == '__main__':
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')

    container = client.containers.get('livivo_base')
    PATH_TAR = '/home/breuert/data/pubmed_subset.tar.xz'
    data = open(PATH_TAR, 'rb').read()
    DST = 'opt/solr/livivo_data/data/'
    container.put_archive(DST, data)

    CMD_INDEX = 'python3 /script/index_init'
    exec_res = container.exec_run(CMD_INDEX)