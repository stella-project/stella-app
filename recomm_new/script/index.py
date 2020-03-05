from gensim.models.doc2vec import Doc2Vec, TaggedDocument
import util
import json
from pyfasttext import FastText
import pandas as pd
import pickle
import multiprocessing
from multiprocessing import Pool,Manager
from multiprocessing import Process, Manager

model_pubset_en = Doc2Vec.load("model/model_en/pubset_en")
model_pubset_de = Doc2Vec.load("model/model_de/pubSet_de_all.model")
model_language = FastText('model/lid.176.ftz')
#*****************************************************
with open("../../data/lini_dic_100_samp_Publication-ALL.json") as f :
    pubs = json.load(f)
    
pubdf=pd.DataFrame(pubs).T


from Item import Item
item = Item()

def isDataset(item):
    if 'research_data'== getType(item):
        return True
    return False

def getType(item_id):
    dictItem = item.get(item_id)
    dictItem = dictItem._source
    return (dictItem["type"])

def getSimilarDataset(idf):
    words = util.get_Vocabs(item,idf)
    res_datast = []
    langg = model_language.predict_proba_single(" ".join(words))
    if (len(langg)==0):
        print(" ".join(words))
    else:
        lang = langg[0][0]
        #print("create infer_vector...")
        if lang=="en":
            paragvector = model_pubset_en.infer_vector(words)
            #paragraph_vectors.append(paragvector)
            result = model_pubset_en.docvecs.most_similar(positive=[paragvector], topn=50)
        else:
            paragvector = model_pubset_de.infer_vector(words)
            #paragraph_vectors.append(paragvector)
            result = model_pubset_de.docvecs.most_similar(positive=[paragvector], topn=50)
            
        #print("filter datasets...")
        res_datast = [(a,b) for (a,b) in result if isDataset(a)][0:10]  
    return res_datast

import multiprocessing as mp
import numpy as np
import json

#pool = mp.Pool(mp.cpu_count())
#similarity_all=[]

num_partitions = 20 #number of partitions to split dataframe
num_cores = mp.cpu_count() #number of cores on your machine
print(num_cores)
num_cores = 15

ids_all = pubdf.index.tolist()
#df_split = np.array_split(ids_all, num_cores, axis=0)

def func(idfs):
    with open('DocVec_similarity_matrix_top_10.txt', 'a') as b:
        b.write(json.dumps({"target_items":idfs,"similar_items":getSimilarDataset(idfs)}))
        b.write("\n")
        b.flush()

pool = Pool(num_cores)
pool.map(func, ids_all)
pool.close()
pool.join()