import requests as req
import json

PORT = '8080'
API = 'http://0.0.0.0:' + PORT + '/stella/api/v1'
ITEM_ID = 'gesis-ssoar-1002'


def main():
    r = req.get(API + '/recommendation/datasets?itemid=' + ITEM_ID)
    print(r.text)


if __name__ == '__main__':
    main()