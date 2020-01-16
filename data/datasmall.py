import pandas as pd
import json
import sys
import os

filename = sys.argv[1]

with open(filename) as json_file:
    data = json.load(json_file)


with open('100_samp_'+os.path.basename(filename), 'w', encoding='utf-8') as f:
    json.dump(data[:100], f, ensure_ascii=False, indent=4)



