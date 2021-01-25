import os

conf = {}

# app settings
conf["app"] = {}

# ranking systems
if os.environ.get("RANKSYS_LIST"):
    conf["app"]["container_list"] = [ranksys for ranksys in os.environ.get("RANKSYS_LIST").split(" ")]
else:
    conf["app"]["container_list"] = ["livivo_base", "livivo_rank_pyserini", "livivo_rank_pyterrier"]  # optionally hard-code a list with experimental ranking systems (cf. recsys)

if os.environ.get("RANKSYS_PRECOM_LIST"):
    conf["app"]["container_precom_list"] = [ranksys for ranksys in os.environ.get("RANKSYS_PRECOM_LIST").split(" ")]
else:
    conf["app"]["container_precom_list"] = ["livivo_rank_precom"]

conf["app"]["container_baseline"] = os.environ.get("RANKSYS_BASE") or "livivo_base" # optionally provide a baseline system (cf. recsys)

# recommmendation systems
if os.environ.get("RECSYS_LIST"):
    conf["app"]["container_list_recommendation"] = [recsys for recsys in os.environ.get("RECSYS_LIST").split(" ")]
else:
    conf["app"]["container_list_recommendation"] = ["gesis_rec_pyserini", "gesis_rec_pyterrier"]

if os.environ.get("RECSYS_PRECOM_LIST"):
    conf["app"]["container_precom_list_recommendation"] = [recsys for recsys in os.environ.get("RECSYS_PRECOM_LIST").split(" ")]
else:
    conf["app"]["container_precom_list_recommendation"] = ["gesis_rec_precom"]

conf["app"]["container_recommendation_baseline"] = os.environ.get("RECSYS_BASE") or "gesis_rec_pyserini"

# create container_dict from list values (easier)
conf["app"]["container_dict"] = {}
for container_name in conf["app"]["container_list"]:
    conf["app"]["container_dict"][container_name] = {"requests": 0}

conf["app"]["container_dict_recommendation"] = {}
for container_name in conf["app"]["container_list_recommendation"]:
    conf["app"]["container_dict_recommendation"][container_name] = {"requests": 0}

conf['app']['DEBUG'] = False
conf['app']['DELETE_SENT_SESSION'] = True if os.environ.get("DELETE_SENT_SESSION") == 'True' else False
conf["app"]["INTERVAL_DB_CHECK"] = int(os.environ.get("INTERVAL_DB_CHECK")) if os.environ.get("INTERVAL_DB_CHECK") else 3  # seconds
conf["app"]["SESSION_EXPIRATION"] = int(os.environ.get("SESSION_EXPIRATION")) if os.environ.get("SESSION_EXPIRATION") else 6  # seconds

server_address = os.environ.get("STELLA_SERVER_ADDRESS") or "nginx"
conf["app"]["STELLA_SERVER_API"] = ' '.join(['http://', server_address, '/stella/api/v1'])
# conf["app"]["STELLA_SERVER_API"] = "http://localhost/stella/api/v1"

conf["app"]["STELLA_SERVER_USER"] = os.environ.get("STELLA_SERVER_USER") or "gesis@stella.org"
conf["app"]["STELLA_SERVER_PASS"] = os.environ.get("STELLA_SERVER_PASS") or "pass"
conf["app"]["STELLA_SERVER_USERNAME"] = os.environ.get("STELLA_SERVER_USERNAME") or "GESIS"

# GESIS
# conf["app"]["STELLA_SERVER_USER"] = "gesis@stella.org"
# conf["app"]["STELLA_SERVER_PASS"] = "pass"
# conf["app"]["STELLA_SERVER_USERNAME"] = "GESIS"

# LIVIVO
# conf["app"]["STELLA_SERVER_USER"] = "livivo@stella.org"
# conf["app"]["STELLA_SERVER_PASS"] = "pass"
# conf["app"]["STELLA_SERVER_USERNAME"] = "LIVIVO"

conf["app"]["INTERLEAVE"] = True if os.environ.get("INTERLEAVE") == 'True' else False
conf['app']['REST_QUERY'] = True
conf['app']['BULK_INDEX'] = True if os.environ.get("BULK_INDEX") == 'True' else False

# logger settings
conf["log"] = {}
conf["log"]["log_path"] = "log"
conf["log"]["log_file"] = "logging.log"

f_in = open('./head/items/gesis.txt', 'r', encoding='utf-8-sig')
conf['app']['head_items'] = [line.strip('\n') for line in f_in.readlines()]
f_in = open('./head/queries/livivo.txt', 'r', encoding='utf-8-sig')
conf['app']['head_queries'] = [line.strip('\n') for line in f_in.readlines()]



