import pyphi
import numpy as np
from toolz import curry, compose, filter

def connected_mechanisms(order, network):
    """Returns an iterable the connected mechanisms of the given order within the given network."""
    return filter(valid_mechanism(order, network.cm), pyphi.utils.powerset(network.node_indices))


def submatrix(array, indices):
    """Return the submatrix of ``array`` corresponding to ``indices``."""
    return array[np.ix_(indices, indices)]


@curry
def valid_mechanism(order, cm, mechanism):
    """Returns True if the mechanism is of the given order or higher and is weakly connected, and False otherwise."""
    return len(mechanism) == order and pyphi.connectivity.is_weak(submatrix(cm, mechanism))
