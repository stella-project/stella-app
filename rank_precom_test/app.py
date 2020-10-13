import xml.etree.ElementTree as ET
from flask import Flask, request, jsonify
import pandas as pd
import os

def query_index(file_path):
    idx = {}
    tree = ET.parse(file_path)
    for hq in tree.findall('head_query'):
        idx[hq.find('query').text] = int(hq.attrib.get('number'))
    return idx


app = Flask(__name__)
q_idx = None
doc_idx = None


@app.route('/test', methods=["GET"])
def test():
    ######################
    ### CUSTOM - START ###
    ######################
    return 'OK', 200
    ####################
    ### CUSTOM - END ###
    ####################


@app.route('/index', methods=["GET"])
def index():
    ######################
    ### CUSTOM - START ###
    ######################
    global q_idx
    q_idx = query_index('./data/topic/head_queries_rnd1.xml')

    global doc_idx

    frames = [pd.read_csv('./data/run/' + file, sep=' ', names=['num', 'Q0', 'docid', 'rank', 'score', 'runid']) for
              file in os.listdir('./data/run/')]
    doc_idx = pd.concat(frames)
    return 'MADE INDEX', 200
    ####################
    ### CUSTOM - END ###
    ####################


@app.route('/ranking', methods=["GET"])
def ranking():
    query = request.args.get('query', None)
    page = request.args.get('page', default=0, type=int)
    rpp = request.args.get('rpp', default=20, type=int)

    response = {}
    response['page'] = page
    response['rpp'] = rpp
    response['query'] = query
    response['num_found'] = 0
    response['itemlist'] = []

    ######################
    ### CUSTOM - START ###
    ######################
    if query in q_idx.keys():
        num = q_idx.get(query)
        ranking = doc_idx[doc_idx['num'] == num]
        response['num_found'] = len(ranking)
        response['itemlist'] = list(ranking['docid'][page*rpp:(page+1)*rpp])
    ####################
    ### CUSTOM - END ###
    ####################

    return jsonify(response)


@app.route('/recommendation/datasets', methods=["GET"])
def rec_data():
    item_id = request.args.get('item_id', None)
    page = request.args.get('page', default=0, type=int)
    rpp = request.args.get('rpp', default=20, type=int)

    response = {}
    response['page'] = page
    response['rpp'] = rpp
    response['item_id'] = item_id
    response['num_found'] = 0
    response['itemlist'] = []
    ######################
    ### CUSTOM - START ###
    ######################
    pass
    ####################
    ### CUSTOM - END ###
    ####################

    return jsonify(response)

@app.route('/recommendation/publications', methods=["GET"])
def rec_pub():
    item_id = request.args.get('item_id', None)
    page = request.args.get('page', default=0, type=int)
    rpp = request.args.get('rpp', default=20, type=int)

    response = {}
    response['page'] = page
    response['rpp'] = rpp
    response['item_id'] = item_id
    response['num_found'] = 0
    response['itemlist'] = []
    ######################
    ### CUSTOM - START ###
    ######################
    pass
    ####################
    ### CUSTOM - END ###
    ####################

    return jsonify(response)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
