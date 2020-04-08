import requests as rq

r = rq.get('http://172.20.0.2:5000/index')
print(r.text)