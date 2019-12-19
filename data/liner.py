import json
import pandas as pd
import sys
import os

filename = sys.argv[1]

with open(filename) as json_file:
	dataset = json.load(json_file)

with open('lini_dic_'+os.path.basename(filename), 'w', encoding="utf-8") as the_file:
	for data in dataset:
		print(data['_source'],file=the_file)
