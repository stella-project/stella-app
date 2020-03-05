from gensim.models.doc2vec import Doc2Vec, TaggedDocument
import util
import json
#from pyfasttext import FastText
import pandas as pd
import pickle
import multiprocessing
from multiprocessing import Pool,Manager
from multiprocessing import Process, Manager
from Item import Item
import multiprocessing as mp
import numpy as np
import json
import ast

class Similar:


    """
        http://0.0.0.0:5555/api/similar?item_id=gesis-bib-135993&cews-2-682517
    """

    def __init__(self):

       
        #self.parser = reqparse.RequestParser()
        #self.parser.add_argument('item_id', action='append', help="item_id cannot be blank!")
        #self.items = items.split('&')
        ABSURL = '/home/tavakons/GWS_REC_UI/recomm_dataset'
        #ABSURL = ''
        self.model_pubset_en = Doc2Vec.load(ABSURL+"/script/model/model_en/pubset_en")
        self.model_pubset_de = Doc2Vec.load(ABSURL+"/script/model/model_de/pubSet_de_all.model")
#        self.model_language = FastText(ABSURL+'/script/model/lid.176.ftz')
        
        with open("../../data/json/publication.json") as f :
            self.pubs = json.load(f)["_source"]
    
        self.pubdf=pd.DataFrame(self.pubs).T
        self.item = Item()
        self.similarity_all_eval=[]
        # self.set_similarity_matrix_top_10()

    def isDataset(item):
        if 'research_data'== getType(item):
            return True
        return False

    def getType(item_id):
        dictItem = self.item.get(item_id)
        dictItem = dictItem._source
        return (dictItem["type"])

    def getSimilarDataset(idf):
        words = util.get_Vocabs(self.item,idf)
        res_datast = []
        langg = self.model_language.predict_proba_single(" ".join(words))
        if (len(langg)==0):
            print(" ".join(words))
        else:
            lang = langg[0][0]
            #print("create infer_vector...")
            if lang=="en":
                paragvector = self.model_pubset_en.infer_vector(words)
                #paragraph_vectors.append(paragvector)
                result = self.model_pubset_en.docvecs.most_similar(positive=[paragvector], topn=50)
            else:
                paragvector = self.model_pubset_de.infer_vector(words)
                #paragraph_vectors.append(paragvector)
                result = self.model_pubset_de.docvecs.most_similar(positive=[paragvector], topn=50)

            #print("filter datasets...")
            res_datast = [(a,b) for (a,b) in result if isDataset(a)][0:10]  
        return res_datast
   
    @staticmethod
    def get_similarity_matrix_top_10():
        #similarity_all = [line.rstrip('\n') for line in open("DocVec_similarity_matrix_top_10.txt")]
        with open('/script/DocVec_similarity_matrix_top_10','rb') as fp:
            similarity_all_eval = pickle.load(fp)
        return similarity_all_eval
        #for sim in similarity_all:
         #   self.similarity_all_eval.append(ast.literal_eval(sim))
        #with open('DocVec_similarity_matrix_top_10', 'wb') as outfile:
         #   pickle.dump(self.similarity_all_eval, outfile)

    
    #def get_similarity_matrix_top_10(self):
     #   return self.similarity_all_eval
    
    def update_similarity_matrix_file():

        num_cores = mp.cpu_count() 
        ids_all = self.pubdf.index.tolist()
        pool = Pool(num_cores)
        pool.map(func, ids_all)
        pool.close()
        pool.join()

    def func(idfs):
        with open('DocVec_similarity_matrix_top_10.txt', 'a') as b:
            b.write(json.dumps({"target_items":idfs,"similar_items":getSimilarDataset(idfs)}))
            b.write("\n")
            b.flush()
