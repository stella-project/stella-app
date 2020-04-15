from flask import Flask, request, jsonify


app = Flask(__name__)


@app.route('/test', methods=["GET"])
def test():
    ######################
    ### CUSTOM - START ###
    ######################
    pass
    ####################
    ### CUSTOM - END ###
    ####################


@app.route('/index', methods=["GET"])
def index():
    ######################
    ### CUSTOM - START ###
    ######################
    pass
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
    pass
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
