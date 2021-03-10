import yaml
import os
import sys


def _mkdir(dir):
    try:
        os.mkdir(dir)
    except OSError as error:
        print(error)


def main():

    '''
    Run this script from the root directory of the 'stella-app':
    python util/idx.py <your-build-file>.yml
    e.g.

    python util/idx.py livivo.yml
    python util/idx.py gesis.yml
    python util/idx.py stella-app.yml

    '''

    yml_path = sys.argv[1]

    with open(yml_path) as file:
        _yml = yaml.load(file)
        service_list = _yml.get('services').keys()
        service_list.remove('db')
        service_list.remove('app')

        for service in service_list:
            path = os.path.join('./index', service)
            _mkdir(path)


if __name__ == '__main__':
    main()
