import requests as rq

QUERY = 'medicine'
r = rq.get('http://172.20.0.2:5000/ranking?query=' + QUERY)
print(r.text)