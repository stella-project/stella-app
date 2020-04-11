import requests as rq

STELLA_URL = 'http://0.0.0.0:8000'
CONT_NAME = 'livivo_elastic'

r = rq.get(STELLA_URL + '/index/' + CONT_NAME)
print(r.text)