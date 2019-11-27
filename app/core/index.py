import docker
import logging
from config import conf

client = docker.DockerClient(base_url='unix://var/run/docker.sock')


def index():
    ''' run indexing methods for all available containers '''
    container_list = list(conf["app"]["container_dict"].keys())

    cmd = 'python /script/index'

    for entry in container_list:
        container = client.containers.get(entry)
        logger = logging.getLogger("stella-app")
        logger.debug(f'Indexing container "{container}"...')
        exec_res = container.exec_run(cmd)
