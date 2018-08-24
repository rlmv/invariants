
import os
import json
import pickle

def state_to_str(state):
    return ''.join(str(x) for x in state)


class Experiment:
    def __init__(self, name, version, network, state):
        self.name = name
        self.version = version
        self.network = network
        self.state = state
    
    @property
    def prefix(self):
        return f"{self.name}_{self.version}_{state_to_str(self.state)}"
    
    @property
    def directory(self):
        return self.prefix

    @property
    def experiment_file(self):
        return os.path.join(self.directory, 'experiment.json')

    @property
    def network_file(self):
        return os.path.join(self.directory, f'{self.prefix}_network.pickle')

    def write_experiment_file(self):
        with open(self.experiment_file, 'w') as f:
            json.dump({'name': self.name,
                       'version': self.version,
                       'state': self.state}, f, indent=2)

    def make_directory(self):
        if not os.path.exists(self.directory):
            os.mkdir(self.directory)
    
    def write_network_file(self):
        with open(self.network_file, 'wb') as f:
            pickle.dump(self.network, f)

    # TODO: make sure it doesn't already exist?
    def initialize(self):
        self.make_directory()
        self.write_experiment_file()
        self.write_network_file()

        
