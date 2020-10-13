import pickle

with open('./queries.pickle', 'rb') as q_pick:
    queries = pickle.load(q_pick)
    top_q = [query[0] for query in queries if query[1] == 1]

    pass
