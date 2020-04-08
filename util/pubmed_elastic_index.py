import docker

if __name__ == '__main__':
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')

    container = client.containers.get('livivo_elastic_base')
    # container = client.containers.get('livivo_elastic')
    CMD_INDEX = 'python3 /script/index'
    exec_res = container.exec_run(CMD_INDEX)