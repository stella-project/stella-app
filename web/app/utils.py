def create_dict_response(
    status=0,
    q_time=0,
    container="",
    params=None,
    sid="",
    rid="",
    ts=0,
    num_found=0,
    page=0,
    rpp=20,
    itemlist=None,
    query="",
):
    # Initialize the default values for mutable types in the function arguments
    if params is None:
        params = {}
    if itemlist is None:
        itemlist = []

    # Create the response dictionary structure
    dict_response = {
        "response_header": {
            "status": status,
            "query": query,
            "q_time": q_time,
            "container": container,
            "ts": ts,
            "params": params,
            "sid": sid,
            "rid": rid,
        },
        "response": {
            "num_found": num_found,
            "page": page,
            "rpp": rpp,
            "items": itemlist,
        },
    }

    return dict_response
