
"""
PyPhi Worker (for Work Queue)

Usage:
  worker.py <network> <state> <infile> <outfile>

Options:
  -h --help     Show this screen.
"""

import sys
import pickle
import pyphi
import numpy as np
from docopt import docopt

from utils import load_pickle, dump_pickle
from master import PartialConcept

def str_to_mechanism(s):
    return tuple(int(n) for n in s.split(','))


def purview_subset(subsystem, direction, mechanism, portion, num_portions):
    purviews = subsystem.potential_purviews(direction, mechanism)

    # Get the candidate purviews for this worker
    # This slice starts at `portion` and gets every element at `num_portions` 
    # intervals afterwards.
    # This is better than taking the first `num_portions` elements, then
    # the second, etc, as this gives all the largest purviews to a single worker.
    return tuple(tuple(purview) for purview in purviews[portion::num_portions])


if __name__ == "__main__":
    arguments = docopt(__doc__)
    network_file = arguments['<network>']
    state = str_to_mechanism(arguments['<state>'])
    infile = arguments['<infile>']
    outfile = arguments['<outfile>']

    # Should be loaded from config file
    # Note: CACHE_REPERTOIRES cannot be configured at runtime
    # and must be loaded from the config file
    assert pyphi.config.MEASURE == 'BLD'
    assert pyphi.config.CACHE_REPERTOIRES == False

    with open(network_file, 'rb') as f:
        network = pickle.load(f)

    subsystem = pyphi.Subsystem(network, state)

    # PartialConcept
    partial = load_pickle(infile)
    mechanism = partial.mechanism

    if partial.remaining_cause_purviews == partial.ALL:
        partial.remaining_cause_purviews = subsystem.potential_purviews(
            pyphi.Direction.CAUSE, mechanism)
        
    if partial.remaining_effect_purviews == partial.ALL:
        partial.remaining_effect_purviews = subsystem.potential_purviews(
            pyphi.Direction.EFFECT, mechanism)
        
    while partial.remaining_cause_purviews:
        cause_purview = partial.remaining_cause_purviews.pop()
        concept = subsystem.concept(mechanism, cause_purviews=(cause_purview,), effect_purviews=())
        partial.merge(concept)
        partial.completed_cause_purviews.append(cause_purview)

    while partial.remaining_effect_purviews:
        effect_purview = partial.remaining_effect_purviews.pop()
        concept = subsystem.concept(mechanism, cause_purviews=(), effect_purviews=(effect_purview,))
        partial.merge(concept)
        partial.completed_effect_purviews.append(effect_purview)

    dump_pickle(outfile, partial)

    print(partial.concept)

    
