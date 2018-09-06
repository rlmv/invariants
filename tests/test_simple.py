
import os
import subprocess
import pyphi
from master import start_master
from utils import Experiment


def test_simple():
    
    network = pyphi.examples.basic_network()
    state = (1,0,0)
    experiment = Experiment('test_simple', '1.0', network, state)
    experiment.initialize()

    mechanisms = pyphi.utils.powerset(network.node_indices, nonempty=True)

    password_file = 'password_file'
    
    print('Starting worker...')
    worker = subprocess.Popen(['work_queue_worker', '-N', experiment.project_name, '-P', password_file])

    try:
        print('Starting master...')
        start_master(experiment, mechanisms, state, 10020, password_file)
    except:
        raise
    finally:
        print('Killing worker...')
        worker.kill()
        worker.wait()

    print('Done.')

    ces = experiment.load_ces()
    print(ces)

    reference_ces = pyphi.compute.ces(pyphi.Subsystem(network, state))
    assert ces.phis == reference_ces.phis
    assert ces.mechanisms == reference_ces.mechanisms

    print('All good!')

    
if __name__ == "__main__":
    test_simple()
