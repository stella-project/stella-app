import json
import pandas as pd
import numpy as np
import util

class Resources:

	def __init__(self):

		with open('/data/lini_dic_100_samp_dataset-ALL.json') as json_file:
			dataset = pd.read_json(json_file)



		with open('/data/lini_dic_100_samp_Publication-ALL.json') as json_file:
			publication = pd.read_json(json_file)


		self.datasets = dataset
		self.publications = publication



	def get_datasets_description(self):
		return  [util.get_description(y) for y in self.datasets["_source"]]

	def get_publications_description(self):
		return  [util.get_description(y) for y in self.publications["_source"]]


	def get_datasets_len(self):
		return len(self.datasets)

	def get_publications_len(self):
		return  len(self.publications)

