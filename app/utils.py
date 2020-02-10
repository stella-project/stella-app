import logging

def create_logger(name, file, loglevel=logging.NOTSET):
	logging.basicConfig(level=loglevel,filename=file, format='%(asctime)s %(levelname)s %(filename)s %(funcName)s - %(message)s')

def create_dict_response(status=0, q_time=0, container='', params={}, sid='',rid='',ts=0, 
						 num_found=0, page=0, results_per_page=20, itemlist=[]):
	dict_response = {}
	dict_response['response_header'] = {}
	dict_response['response'] = {}

	dict_response['response_header']['status'] = status
	dict_response['response_header']['q_time'] = q_time
	dict_response['response_header']['container'] = container
	dict_response['response_header']['ts'] = ts
	dict_response['response_header']['params'] = params
	'''
	if "page" in params:
		page = int(params['page'])

	if "results_per_page" in params:
		results_per_page = int(params['results_per_page'])
	'''
	dict_response['response']['num_found'] = num_found
	dict_response['response']['page'] = page
	dict_response['response']['results_per_page'] = results_per_page
	#i = page*results_per_page
	#j = page*results_per_page+results_per_page

	dict_response['response']['itemlist'] = itemlist

	#try:
	#	dict_response['response']['itemlist'] = itemlist[i:j]
	#except:
	#	dict_response['response']['itemlist'] = itemlist[0,results_per_page]

	return dict_response  
