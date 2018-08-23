
import glob
from master import load_pickle, hms

if __name__ == "__main__":
    
    ces = []
    directory = 'largepyr_2.1_00000000000000000000'

    for path in glob.glob(f'{directory}/*.pickle'):
        if 'network' not in path:
            concept = load_pickle(path)
            if concept.phi > 0:
                ces.append(concept)
    
    for concept in ces:
        print("{:4}{:<12}{}".format(
                ''.join(concept.node_labels.indices2labels(concept.mechanism)), 
                concept.phi,
                hms(concept.time)))
