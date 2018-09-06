
"""
PyPhi Worker (for Work Queue)

Usage:
  worker.py <network> <state> <infile> <outfile> <timeout>

Options:
  -h --help     Show this screen.
"""

import sys
import pickle
import pyphi
import numpy as np
from time import time
from docopt import docopt

from utils import load_pickle, dump_pickle
from master import PartialConcept

def str_to_mechanism(s):
    return tuple(int(n) for n in s.split(','))


if __name__ == "__main__":
    arguments = docopt(__doc__)
    network_file = arguments['<network>']
    state = str_to_mechanism(arguments['<state>'])
    infile = arguments['<infile>']
    outfile = arguments['<outfile>']
    timeout = int(arguments['<timeout>'])

    start_time = time()
    def timed_out():
        return time() - start_time > timeout

    # Should be loaded from config file
    # Note: CACHE_REPERTOIRES cannot be configured at runtime
    # and must be loaded from the config file
    assert pyphi.config.MEASURE == 'BLD'
    assert pyphi.config.CACHE_REPERTOIRES == False

    network = load_pickle(network_file)
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
        concept = subsystem.concept(mechanism, purviews=(), 
                                    cause_purviews=(cause_purview,), 
                                    effect_purviews=())
        
        partial.merge_concept(concept)
        partial.completed_cause_purviews.append(cause_purview)

        if timed_out():
            print('Timed out')
            break

    while partial.remaining_effect_purviews:
        effect_purview = partial.remaining_effect_purviews.pop()
        concept = subsystem.concept(mechanism, purviews=(), 
                                    cause_purviews=(), 
                                    effect_purviews=(effect_purview,))
        partial.merge_concept(concept)
        partial.completed_effect_purviews.append(effect_purview)
        
        if timed_out():
            print('Timed out')
            break
        
    dump_pickle(outfile, partial)
    print(partial.concept)

    
