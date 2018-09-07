
import os
import subprocess
import pyphi
from master import WorkerFactory, start_master
from utils import Experiment

def test_factory():

    # Generate the network & experiment.
    # This should generally be done in a separate script
    network = pyphi.examples.basic_network()
    state = (1, 0, 0)
    experiment = Experiment('test_factory', '1.0', network, state)
    experiment.initialize()

    port = 10030
    mechanisms = pyphi.utils.powerset(network.node_indices, nonempty=True)

    with WorkerFactory(experiment) as factory:
        start_master(experiment, mechanisms, port)

    # Load CES
    ces = experiment.load_ces()
    print(ces)

    # Check results
    reference_ces = pyphi.compute.ces(pyphi.Subsystem(network, state))
    assert ces.phis == reference_ces.phis
    assert ces.mechanisms == reference_ces.mechanisms

    print('All good!')


if __name__ == '__main__':
    test_factory()
    
