conf = {}

# app settings
conf["app"] = {}
conf["app"]["container_list"] = ["elastic"]

# create container_dict from list values (easier)
conf["app"]["container_dict"] = {}
for container_name in conf["app"]["container_list"]:
    conf["app"]["container_dict"][container_name] = {"requests":0}

'''
conf["app"]["container_dict"] = {"lucene": {"requests": 0},
                                 "solr": {"requests": 0}}
'''


# logger settings
conf["log"] = {}
conf["log"]["log_path"] = "log"
conf["log"]["log_file"] = "logging.log"