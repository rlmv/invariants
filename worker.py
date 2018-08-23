
"""
PyPhi Worker (for Work Queue)

Usage:
  worker.py <network> <state> <mechanism> <outfile>

Options:
  -h --help     Show this screen.
"""

import sys
import pickle
import pyphi
from docopt import docopt


def str_to_mechanism(s):
    return tuple(int(n) for n in s.split(','))


if __name__ == "__main__":
    arguments = docopt(__doc__)
    network_file = arguments['<network>']
    state = str_to_mechanism(arguments['<state>'])
    mechanism = str_to_mechanism(arguments['<mechanism>'])
    outfile = arguments['<outfile>']

    pyphi.config.MEASURE = 'BLD'
    pyphi.config.CACHE_REPERTOIRES = False

    with open(network_file, 'rb') as f:
        network = pickle.load(f)

    subsystem = pyphi.Subsystem(network, state)

    with open(outfile, 'wb') as f:
        concept = subsystem.concept(mechanism)

        # Remove extra data
        concept.subsystem = None  
        concept.cause.ria._repertoire = None
        concept.cause.ria._partitioned_repertoire = None
        concept.effect.ria._repertoire = None
        concept.effect.ria._partitioned_repertoire = None

        pickle.dump(concept, f)

    
