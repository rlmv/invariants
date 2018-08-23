
import glob
from master import load_pickle, hms

if __name__ == "__main__":
    
    def concept_name(concept):
        return ''.join(concept.node_labels.indices2labels(concept.mechanism))

    directory = 'largepyr_2.1_00000000000000000000'
    ces = []
    runtimes = {} 

    print('CES:')

    for path in glob.glob(f'{directory}/*.pickle'):
        if 'network' not in path:
            concept = load_pickle(path)
            if concept.phi > 0:
                ces.append(concept)
            runtimes[concept_name(concept)] = concept.time
    
    for concept in ces:
        print("{:4}{:<12}{}".format(
                concept_name(concept),
                concept.phi,
                hms(concept.time)))

    print()
    print('Longest computation times:')

    for name, time in sorted(runtimes.items(), key=lambda x: x[1], reverse=True)[:20]:
        print("{:4}{}".format(name, hms(time)))
