import requests as req

PORT = '8000'
API = 'http://0.0.0.0:' + PORT + '/stella/api/v1'
QUERY = 'study'
SID = 1


def main():
    r = req.put(API + '/sessions/' + str(SID) + '/exit')
    print(r.status_code)


if __name__ == '__main__':
    main()
