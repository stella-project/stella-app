from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
import json
import os
import ast

PATH = '/data/index'
INDEX = 'idx'
app = Flask(__name__)


@app.route('/test', methods=["GET"])
def test():
    ######################
    ### CUSTOM - START ###
    ######################
    es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
    return es.info(), 200
    ####################
    ### CUSTOM - END ###
    ####################


@app.route('/index', methods=["GET"])
def index():
    ######################
    ### CUSTOM - START ###
    ######################
    es = Elasticsearch([{'host': 'localhost',
                         'port': 9200}])
    docs = 0

    for file in os.listdir(PATH):
        if file.endswith(".jsonl"):
            with open(os.path.join(PATH, file), 'r', encoding="utf-8") as f:
                for line in f:
                    try:
                        doc = ast.literal_eval(line)
                        es.index(index=INDEX, doc_type=doc['type'], id=doc['id'], body=doc)
                        docs += 1
                    except:
                        pass

    return 'Index built with ' + str(docs) + ' docs', 200
    ####################
    ### CUSTOM - END ###
    ####################


@app.route('/ranking', methods=["GET"])
def ranking():
    query = request.args.get('query', None)
    page = request.args.get('page', default=0, type=int)
    rpp = request.args.get('rpp', default=20, type=int)

    start = page*rpp

    response = {}
    response['page'] = page
    response['rpp'] = rpp
    response['query'] = query
    response['num_found'] = 0
    response['itemlist'] = []

    ######################
    ### CUSTOM - START ###
    ######################
    if (query is not None):

        es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

        result = es.search(index=INDEX,
                           from_=start,
                           size=rpp,
                           body={"query": {"query_string": {"query": query, "default_field": "*"}}})

        for res in result["hits"]["hits"]:
            try:
                response['itemlist'].append(res['_source']['id'])
            except:
                pass

        response['num_found'] = len(result["hits"]["hits"])
    ####################
    ### CUSTOM - END ###
    ####################

    return jsonify(response)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
