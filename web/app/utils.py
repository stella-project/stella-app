def create_dict_response(
    status=0,
    q_time=0,
    container="",
    params={},
    sid="",
    rid="",
    ts=0,
    num_found=0,
    page=0,
    rpp=20,
    itemlist=[],
    query="",
):
    dict_response = {}
    dict_response["response_header"] = {}
    dict_response["response"] = {}

    dict_response["response_header"]["status"] = status
    dict_response["response_header"]["query"] = query
    dict_response["response_header"]["q_time"] = q_time
    dict_response["response_header"]["container"] = container
    dict_response["response_header"]["ts"] = ts
    dict_response["response_header"]["params"] = params
    dict_response["response_header"]["sid"] = sid
    dict_response["response_header"]["rid"] = rid
    """
	if "page" in params:
		page = int(params['page'])

	if "rpp" in params:
		rpp = int(params['rpp'])
	"""
    dict_response["response"]["num_found"] = num_found
    dict_response["response"]["page"] = page
    dict_response["response"]["rpp"] = rpp
    # i = page*rpp
    # j = page*rpp+rpp

    dict_response["response"]["items"] = itemlist

    # try:
    # 	dict_response['response']['itemlist'] = itemlist[i:j]
    # except:
    # 	dict_response['response']['itemlist'] = itemlist[0,rpp]

    return dict_response
