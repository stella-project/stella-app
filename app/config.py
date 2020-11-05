conf = {}

# app settings
conf["app"] = {}
conf["app"]["container_list"] =  ["dummy_rank", "dummy_rank_base"]
conf["app"]["container_list_recommendation"] = ["gesis_rec_micro", "gesis_rec_precom"]
conf["app"]["container_baseline"] = "dummy_rank_base"
conf["app"]["container_recommendation_baseline"] = "gesis_rec_micro"

# create container_dict from list values (easier)
conf["app"]["container_dict"] = {}
for container_name in conf["app"]["container_list"]:
    conf["app"]["container_dict"][container_name] = {"requests": 0}

conf["app"]["container_dict_recommendation"] = {}
for container_name in conf["app"]["container_list_recommendation"]:
    conf["app"]["container_dict_recommendation"][container_name] = {"requests": 0}

conf['app']['DEBUG'] = False
conf['app']['DELETE_SENT_SESSION'] = True
conf["app"]["INTERVAL_DB_CHECK"] = 3  # seconds
conf["app"]["SESSION_EXPIRATION"] = 6  # seconds

conf["app"]["STELLA_SERVER_API"] = "http://nginx/stella/api/v1"
# conf["app"]["STELLA_SERVER_API"] = "http://localhost/stella/api/v1"
conf["app"]["STELLA_SERVER_USER"] = "site_a@stella.org"
conf["app"]["STELLA_SERVER_PASS"] = "pass"
conf["app"]["STELLA_SERVER_USERNAME"] = "site_a"
conf["app"]["INTERLEAVE"] = True
conf['app']['REST_QUERY'] = True
conf['app']['BULK_INDEX'] = True

# logger settings
conf["log"] = {}
conf["log"]["log_path"] = "log"
conf["log"]["log_file"] = "logging.log"
