import random
import uuid

with open('precomputed.txt', 'w') as run:
    for i in range(1, 26):
        for j in range(0,1000):
            run.write(str(i) + ' Q0 ' + str(j+1) + ' ' + uuid.uuid4().hex + ' ' + str(random.uniform(1000-(j+1), 1000-j) / 1000) + ' ' + 'run_id' + '\n')