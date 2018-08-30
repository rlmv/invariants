
"""
PyPhi Worker (for Work Queue)

Usage:
  worker.py <network> <state> <mechanism> <outfile> [--purview-portion=<i:num_portions>]

Options:
  -h --help     Show this screen.
"""

import sys
import pickle
import pyphi
import numpy as np
from docopt import docopt


def str_to_mechanism(s):
    return tuple(int(n) for n in s.split(','))


def purview_subset(subsystem, direction, mechanism, portion, num_portions):
    purviews = subsystem.potential_purviews(direction, mechanism)
    print(f'All {direction} purviews: {purviews}')

    # Get the candidate purviews for this worker
    # This slice starts at `portion` and gets every element at `num_portions` 
    # intervals afterwards.
    # This is better than taking the first `num_portions` elements, then
    # the second, etc, as this gives all the largest purviews to a single worker.
    candidates = purviews[portion::num_portions]
    print(f'Portion {portion}:{num_portions} {candidates}')

    return candidates


if __name__ == "__main__":
    arguments = docopt(__doc__)
    network_file = arguments['<network>']
    state = str_to_mechanism(arguments['<state>'])
    mechanism = str_to_mechanism(arguments['<mechanism>'])
    outfile = arguments['<outfile>']

    purview_portion = arguments['--purview-portion']

    # Should be loaded from config file
    # Note: CACHE_REPERTOIRES cannot be configured at runtime
    # and must be loaded from the config file
    assert pyphi.config.MEASURE == 'BLD'
    assert pyphi.config.CACHE_REPERTOIRES == False

    with open(network_file, 'rb') as f:
        network = pickle.load(f)

    subsystem = pyphi.Subsystem(network, state)

    if purview_portion is not None:
        portion, num_portions = [int(p) for p in purview_portion.split(':')]
        cause_purviews = purview_subset(subsystem, pyphi.Direction.CAUSE, mechanism, portion, num_portions)
        effect_purviews = purview_subset(subsystem, pyphi.Direction.EFFECT, mechanism, portion, num_portions)
    else:
        cause_purviews = False
        effect_purviews = False

    concept = subsystem.concept(mechanism, cause_purviews=cause_purviews, effect_purviews=effect_purviews)
    print(concept)

    # Remove extra data
    concept.subsystem = None  
    concept.cause.ria._repertoire = None
    concept.cause.ria._partitioned_repertoire = None
    concept.effect.ria._repertoire = None
    concept.effect.ria._partitioned_repertoire = None
        
    with open(outfile, 'wb') as f:
        pickle.dump(concept, f)

    
