
import glob
from master import load_pickle, hms
import sys

import matplotlib
import pandas as pd
#matplotlib.use('Agg')

if __name__ == "__main__":
    
    def concept_name(concept):
        #TODO remove this
        return concept.mechanism
        return ''.join(concept.node_labels.indices2labels(concept.mechanism))

    directory = sys.argv[1]
    ces = []
    runtimes = {} 

    print('CES:')

    for path in glob.glob(f'{directory}/*.pickle'):
        if 'network' not in path:
            concept = load_pickle(path)
            # TODO: remove
            concept.mechanism = path.split('/')[1].split('.')[0]
            if concept.phi > 0:
                ces.append(concept)
            runtimes[concept_name(concept)] = concept.time
    
    for concept in sorted(ces, key=lambda x: (len(x.mechanism), x.mechanism)):
        print("{:6}{:<12}{}".format(
                concept_name(concept),
                concept.phi,
                hms(concept.time)))

    print()
    print('Longest computation times:')

    for name, time in sorted(runtimes.items(), key=lambda x: x[1], reverse=True)[:20]:
        print("{:6}{}".format(name, hms(time)))
