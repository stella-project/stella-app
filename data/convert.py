import os
import ast
import json
import jsonlines

LIVIVO_RAW = './livivo/pubmed_2015_2016.jsonl'
LIVIVO_OUT = './convert/livivo.jsonl'
GESIS_RAW = './lini_dic_100_samp_Publication-ALL.json'
GESIS_OUT = './convert/gesis.jsonl'

if __name__ == '__main__':

    if not os.path.exists('./convert'):
        os.makedirs('./convert')

    with open(LIVIVO_RAW) as jl:
        with jsonlines.open(LIVIVO_OUT, mode='w') as writer:
            for line in jl:
                j = json.loads(line)
                writer.write({'title': j['TITLE'][0],
                              'id': j['DBRECORDID'],
                              'date': j['PUBLYEAR'][0],
                              'type': j['DOCTYPE'][0],
                              'abstract': (j.get('ABSTRACT')[0] if j.get('ABSTRACT') is not None else 'no abstract'),
                              'person': (j.get('AUTHOR')[0] if j.get('AUTHOR') is not None else 'no authors'),
                              'publisher': j['SOURCE'][0],
                              'links': {'doi': j['DOI'][0]}})

    with open(GESIS_RAW) as jl:
        with jsonlines.open(GESIS_OUT, mode='w') as writer:
            for line in jl:
                j = ast.literal_eval(line)
                writer.write({'title': j['title'],
                              'id': j['id'],
                              'date': j['date'],
                              'type': j['type'],
                              'abstract': (j.get('abstract') if j.get('abstract') is not None else 'no abstract'),
                              'person': (j.get('person') if j.get('person') is not None else 'no authors'),
                              'publisher': (j.get('source') if j.get('source') is not None else 'no source'),
                              'links': (j.get('links') if j.get('links') is not None else 'no links')})


