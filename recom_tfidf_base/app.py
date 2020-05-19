from flask import Flask, request, jsonify
import os
import json
import pickle
import random

JL_PATH = './data/index'
app = Flask(__name__)
cos_sim_mat = None
corpus = None


def index_data(jl_path):
    corpus = {}
    with open(jl_path) as jl:
        for line in jl:
            j = json.loads(line)
            corpus[j['id']] = json.loads(line)
    return corpus


@app.route('/test', methods=["GET"])
def test():
    ######################
    ### CUSTOM - START ###
    ######################
    print("tfidf vectorizer!")
    ####################
    ### CUSTOM - END ###
    ####################


@app.route('/index', methods=["GET"])
def index():
    ######################
    ### CUSTOM - START ###
    ######################
    global cos_sim_mat
    cos_sim_mat = pickle.load(open("cosine_similarity_matrix_top_10.pkl", "rb"))
    global corpus
    for file in os.listdir(JL_PATH):
        if file.endswith(".jsonl"):
            corpus = index_data(os.path.join(JL_PATH, file))
    ####################
    ### CUSTOM - END ###
    ####################


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

    result = [sim for sim in cos_sim_mat if sim["target_items"] == item_id][0]['similar_items']
    response['itemlist'] = [{"id": k, "detail": {"score": v, "reason": ""}} for k, v in result.items()]

    # pass
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
    ######################
    ### CUSTOM - START ###
    ######################
    response['itemlist'] = random.choices(list(corpus.keys()), k=rpp)
    ####################
    ### CUSTOM - END ###
    ####################

    return jsonify(response)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
