import json
from Item import Item
from gensim.utils import simple_preprocess
import pandas as pd
import numpy as np



TAGS_PUBLICATIONS = ["title_en", "title", "topic", "topic_en","abstract_en", "abstract"]
TAGS_DATASET = ["title_en", "title", "topic", "topic_en","abstract_en", "abstract"]



def getItemShortRepresentation(itemid):
    item = Item()
    dictItem = item.get(itemid)
    source = dictItem["_source"]
    return {"id": itemid,
            "title": source["title"],
            "item_type": source["type"]}


def getSimilarItemShortRepresentation(similarItem):

    """
    :param similarItem: similar item is an array of two element, item_id(string) and the similarity rate(float)
    :return: a dict of similar item title and item type
    """
    
    item = Item()
    dictItem = item.get(similarItem[0])
    source = dictItem["_source"]
    return {"id": similarItem[0],
            "title": source["title"],
            "item_type": source["type"],
	    "similarity_rate":similarItem[1]}

def getType(item_id):
    item = Item()
    dictItem = item.get(item_id)
    dictItem = dictItem._source
    return (dictItem["type"])
    

def get_Vocabs(item,item_id):

    #dictItem = next((x for x in pubsetlist if item_id in x["_id"] ), None)
    #item = Item()
    content=""
    
    dictItem = item.get(item_id)
    if dictItem.any():
        dictItem = dictItem._source
        itemtype = dictItem["type"]
        if itemtype == "publication":
            content = getMetadata_String(dictItem, TAGS_PUBLICATIONS)
        elif itemtype == "research_data":
            content = getMetadata_String(dictItem, TAGS_DATASET)

        words= simple_preprocess(content)
        return words
    else:
        return None


def getMetadata_String(item, tags):

    paragraph= [item["type"]]
    for tag in tags:
        if tag in item:
            if  isinstance(item[tag], (list,)):
               paragraph.append((' '.join(item[tag])))
            else:
               paragraph.append(item[tag])

    return ' '.join(paragraph)

def get_description(y):
    try:
        if isinstance(y["title"], (list,)):
            return {"id": y["id"], "title": ' '.join(y["title"])}
        else:
            return {"id": y["id"], "title": y["title"]}
    except:
        pass


