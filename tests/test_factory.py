
import os
import subprocess
import pyphi
from master import WorkerFactory, start_master, generate_password_file
from utils import Experiment

def test_factory():

    # Generate the network & experiment.
    # This should generally be done in a separate script
    network = pyphi.examples.basic_network()
    state = (1, 0, 0)
    experiment = Experiment('test_factory', '1.0', network, state)
    experiment.initialize()

    project_name = experiment.prefix
    password_file = 'test_factory_password_file'
    generate_password_file(password_file)
    port = 10030
    mechanisms = pyphi.utils.powerset(network.node_indices, nonempty=True)

    with WorkerFactory(experiment, project_name, password_file) as factory:
        start_master(experiment, mechanisms, state, project_name, port, password_file)

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
    
