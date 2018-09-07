
import os
import json
import glob
import pickle
import random
import string
from getpass import getuser

import pyphi

def state_to_str(state):
    return ''.join(str(x) for x in state)

def load_pickle(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)


def dump_pickle(filename, obj):
    with open(filename, 'wb') as f:
        pickle.dump(obj, f)


def generate_password_file(filename, length=50):
    """
    Randomly generate a password file.
    """
    characters = string.ascii_letters + string.digits

    with open(filename, 'w') as f:
        for i in range(length):
            f.write(random.choice(characters))


class Experiment:
    def __init__(self, name, version, network, state):
        self.name = name
        self.version = version
        self.network = network
        self.state = state

    def __str__(self):
        return self.prefix
    
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

    @property
    def project_name(self):
        '''Work queue project name, used for catalog server.

        This adds the user name in case multiple people are running the same
        experiment.'''
        return f'{self.prefix}_{getuser()}'

    @property
    def password_file(self):
        filename = f'{self}_password'
        if not os.path.exists(filename):
            generate_password_file(filename)
        else:
            print('Password file already exists')
        return filename

    @property
    def stats_log_file(self):
        return f'{self}.stats.log'

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

    def load_ces(self):
        concepts = []
        for path in glob.iglob(f'{self.directory}/*.pickle'):
            if not path == self.network_file:
                concept = load_pickle(path)
                if concept.phi > 0:
                    concepts.append(concept)
        
        return pyphi.models.CauseEffectStructure(concepts)

        


class PartialConcept:
    ALL = '__all__'

    def __init__(self, mechanism):
        self.mechanism = mechanism

        self.remaining_cause_purviews = self.ALL
        self.remaining_effect_purviews = self.ALL

        self.completed_cause_purviews = []
        self.completed_effect_purviews = []
        
        self.concept = None

    @property
    def unfinished(self):
        return self.remaining_cause_purviews or self.remaining_effect_purviews
        
    def merge_concept(self, other):
        if self.concept is None:
            self.concept = other
        else:
            self.concept.cause = max(self.concept.cause, other.cause)
            self.concept.effect = max(self.concept.effect, other.effect)
            self.concept.time = self.concept.time + other.time

        # Remove extra data
        self.concept.subsystem = None  
        self.concept.cause.ria._repertoire = None
        self.concept.cause.ria._partitioned_repertoire = None
        self.concept.effect.ria._repertoire = None
        self.concept.effect.ria._partitioned_repertoire = None

        return self

    def merge_partial(self, other):
        self.merge_concept(other.concept)
        self.completed_cause_purviews += other.completed_cause_purviews
        self.completed_effect_purviews += other.completed_effect_purviews

        # TODO: convert to lists
        self.remaining_cause_purviews = set(self.remaining_cause_purviews).union(other.remaining_cause_purviews) - set(self.completed_cause_purviews)

        self.remaining_effect_purviews = set(self.remaining_effect_purviews).union(other.remaining_effect_purviews) - set(self.completed_effect_purviews)
        return self

    def divide(self, n):
        """Split this task into ``n`` new tasks."""
        for i in range(n):
            c = PartialConcept(self.mechanism)
            c.remaining_cause_purviews = self.remaining_cause_purviews[i::n]
            c.remaining_effect_purviews = self.remaining_effect_purviews[i::n]
            # completed_purviews are empty lists

            if c.unfinished:
                yield c
