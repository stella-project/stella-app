conf = {}

# app settings
conf["app"] = {}
conf["app"]["container_list"] = ["livivo_elastic", "livivo_elastic_base"]
conf["app"]["container_list_recommendation"] = ["recom_tfidf"]
conf["app"]["container_baseline"] = "livivo_elastic_base"
conf["app"]["container_recommendation_baseline"] = "recom_tfidf"

# create container_dict from list values (easier)
conf["app"]["container_dict"] = {}
for container_name in conf["app"]["container_list"]:
    conf["app"]["container_dict"][container_name] = {"requests": 0}

conf["app"]["container_dict_recommendation"] = {}
for container_name in conf["app"]["container_list_recommendation"]:
    conf["app"]["container_dict_recommendation"][container_name] = {"requests": 0}

conf['app']['DEBUG'] = True
conf['app']['DELETE_SENT_SESSION'] = True
conf["app"]["INTERVAL_DB_CHECK"] = 3  # seconds
conf["app"]["SESSION_EXPIRATION"] = 30  # seconds

conf["app"]["STELLA_SERVER_API"] = "http://localhost:8080/stella/api/v1"
conf["app"]["STELLA_SERVER_USER"] = "site_a@stella.org"
conf["app"]["STELLA_SERVER_PASS"] = "pass"
conf["app"]["STELLA_SERVER_USERNAME"] = "Site A"
conf["app"]["INTERLEAVE"] = True
conf['app']['REST_QUERY'] = True

# logger settings
conf["log"] = {}
conf["log"]["log_path"] = "log"
conf["log"]["log_file"] = "logging.log"
