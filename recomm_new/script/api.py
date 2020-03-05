from flask import Flask, request
from flask_restful import Resource, Api

import json
from Similar import Similar
import ast



class Recommand(Resource):
    

    def __init__(self):
        similar = Similar()
        similarity_all_eval = similar.get_similarity_matrix_top_10()
        print(len(similarity_all_eval))

    def get(self,doc_id):
        return self.getsimilarityjson(doc_id)

    def getsimilarityjson(self,id):
        try:
            return id
            return [sim for sim in similarity_all_eval if sim['target_items']==id][0]
        except:
            return None


app = Flask(__name__)
api = Api(app)

api.add_resource(Recommand, '/<string:doc_id>')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9210, debug=True)
