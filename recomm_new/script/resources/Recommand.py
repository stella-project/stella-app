from flask_restful import Resource
import json
from Similar import Similar
import ast



class Recommand(Resource):

    def __init__(self):
        similar = Similar()
        similarity_all_eval = similar.get_similarity_matrix_top_10()
        print(len(similarity_all_eval))
        
    def get(self,doc_id):
        return getsimilarityjson(doc_id)
    
    def getsimilarityjson(id):
        try:
            return [sim for sim in similarity_all_eval if sim['target_items']==id][0]
        except:
            return None
