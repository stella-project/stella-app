import requests as req
import json

PORT = '8000'
API = 'http://0.0.0.0:' + PORT + '/stella/api/v1'
QUERY = 'study'
SID = 1


def main():
    r = req.get(API + '/ranking?query=' + QUERY + '&sid=' + str(SID))
    print(r.text)


if __name__ == '__main__':
    main()
