from Resources import Resources

class Item():

	def __init__(self):
		self.resources = Resources()

	def get(self,item_id):

		try:		
			return self.resources.datasets.loc[item_id]
		except: 
			try:
				return self.resources.publications.loc[item_id]
			except:
				return None			
		
