from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
import json
import os
import ast

PATH = './data/'
app = Flask(__name__)

for file in os.listdir(PATH):
    if file.endswith(".jsonl"):
        with open(os.path.join(PATH, file), 'r', encoding="utf-8") as f:
            for line in f:
                # doc = json.loads(f)
                try:
                    doc = ast.literal_eval(line)
                    pass
                except:
                    # print(doc['id'])
                    pass