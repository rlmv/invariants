#!/usr/bin/env cctools_python
# CCTOOLS_PYTHON_VERSION 2.7 2.6

# Copyright (c) 2010- The University of Notre Dame.
# This software is distributed under the GNU General Public License.
# See the file COPYING for details.

from work_queue import *

from uuid import uuid4
import random
import itertools
import os
import sys
import pickle
import glob
import subprocess
import pyphi
from time import time
from utils import Experiment, load_pickle, dump_pickle

# To start the master:
#
#    python master.py 
# 
# To start a local worker:
#
#    work_queue_worker -N PROJECT_NAME -P PASSWORD_FILE
#
# or 10 distributed workers on Condor:
#
#    condor_submit_workers -N invariants -P password_file --memory 2048 10
#

# Be sure to increase the memory allocation! Default is 512 MB, which is not
# sufficient for PyPhi tasks. The network and subsystem TPMs are already
# 160 MB each for a 20-node network.
#
# Runtime for a 20-node network: 
#
#  order  mins
# +-----+------+
# | 1st | 4-6  |
# +-----+------+
# | 2nd | 6-12 |
# +-----+------+
# |     |      |
# +-----+------+


def to_secs(mcs):
    """Convert microseconds to seconds."""
    return mcs / (10 ** 6)


def hms(sec_elapsed):
    """Convert seconds to hours-minutes-seconds."""
    h = int(sec_elapsed / (60 * 60))
    m = int((sec_elapsed % (60 * 60)) / 60)
    s = sec_elapsed % 60
    return "{}:{:>02}:{:>02.0f}".format(h, m, s)


def _outfile(mechanism):
    return "{}.out".format(mechanism_to_str(mechanism))


def mechanism_to_str(mechanism):
    return ','.join(str(n) for n in mechanism)


def mechanism_to_labels(network, mechanism):
    return ''.join(network.node_labels.indices2labels(mechanism))


class WorkerFactory:
    """
    A work queue factory pool.
    
    Use as a context manager, eg:
    
        with WorkerFactory(...) as factory:
            start_master(...)
    """
    def __init__(self, experiment):
        self.experiment = experiment
        self.process = None

    def __enter__(self):
        log_file = open(f'{self.experiment}.factory.out', 'w+')

        print('Starting worker factory...')
        self.process = subprocess.Popen([
                'nohup',
                'work_queue_factory', 
                '--master-name', self.experiment.project_name,
                '--password', self.experiment.password_file, 
                '--memory', '4096',
                '--batch-type', 'condor',
                '--max-workers', '1000',
                '-d', 'wq',
                '--capacity',  # Provide as many workers as useful
                '--workers-per-cycle', '10'
                ], stdout=log_file, stderr=log_file)
    
    def __exit__(self, *exc):
        print('Killing factory...')
        self.process.kill()
        self.process.wait()
        print('Done.')


N_PORTIONS = 2

class ConceptTask(Task):

    def __init__(self, experiment, network, state, mechanism):
        self.experiment = experiment
        self.network = network
        self.mechanism = mechanism
        self.state = state

        # Unique ID for this task
        # Work Queue tasks also have an `id`, but this is not generated
        # until the task is submitted
        self.uuid = uuid4()
        
        super().__init__(self.command)

    @property
    def command(self):
        return "sh worker.sh {} {} {} {}".format(
                self.experiment.network_file,
                mechanism_to_str(self.state),
                mechanism_to_str(self.mechanism),
                self.remote_outfile)

    @property
    def remote_outfile(self):
        return "{}.pickle".format(mechanism_to_labels(self.network, self.mechanism))

    @property
    def result_file(self):
        return f'{self.experiment.directory}/{self.remote_outfile}'

    @property
    def local_outfile(self):
        return f'{self.result_file}.part:{self.uuid}'

    def merge_results(self):
        # If the cumulative a master outfile does not exist, make the output
        # of this task 
        # if not os.path.exists(self.result_file):
        #     shutil.move(self.local_outfile, self.result_file)
        #     return 
        completed_parts = glob.glob(f'{self.result_file}.part:*')
        
        concept_filename = completed_parts.pop()
        concept = load_pickle(concept_filename)

        for part_filename in completed_parts:
            print(f'Merging {part_filename} into {concept_filename}')
            part = load_pickle(part_filename)
            
            # TODO: deal with completed purviews
            concept.cause = max(concept.cause, part.cause)
            concept.effect = max(concept.effect, part.effect)
            concept.time = concept.time + part.time

        dump_pickle(concept_filename, concept)

        print(f'Removing partial files {completed_parts}')
        os.remove(*completed_parts)
            

def start_master(experiment, mechanisms, state, port):

    print(f'Starting {experiment.project_name}...')
    start_time = time()

    network = load_pickle(experiment.network_file)

    def fmt_portion(portion, num_portions):
        return f'{portion}:{num_portions}'

    def partial(portion, num_portions):
        return f'.part:{fmt_portion(portion, num_portions)}'

    def remote_file(mechanism):
        return "{}.pickle".format(mechanism_to_labels(network, mechanism))

    def local_file(mechanism):
        return os.path.join(experiment.directory, remote_file(mechanism))

    input_files = [
        'miniconda.tar.gz',
        'worker.sh',
        'worker.py',
        'pyphi_config.yml',
        experiment.network_file
     ]
    
    for filename in input_files:
        if not os.path.exists(filename):
            print(f'Input file {filename} not found')
            sys.exit(1)

    q = WorkQueue(port)
    
    # Enable debug logging
    # cctools_debug_flags_set("all")
    q.specify_log(experiment.stats_log_file)

    # Identify our master via a catalog server
    # so we can pass `-N PROJECT_NAME` to condor_submit_worker
    q.specify_master_mode(WORK_QUEUE_MASTER_MODE_CATALOG)
    q.specify_name(experiment.project_name)
    
    # Enable password file
    q.specify_password_file(experiment.password_file)

    print("Listening on port %d..." % q.port)

    for mechanism in mechanisms:
        mechanism = tuple(mechanism)
        mechanism_labels = mechanism_to_labels(network, mechanism)
        
        t = ConceptTask(experiment, network, state, mechanism)

        if os.path.exists(t.result_file):
            print('Skipping mechanism', mechanism_labels)
            continue

        # Else: check if partial files exist

        # if os.path.exists(t.local_outfile):
        #     print('Skipping purview portion', portion, N_PORTIONS)
        #     continue

        for filename in input_files:
            t.specify_input_file(filename, filename, cache=True)

        # Output files are typically not cached
        t.specify_output_file(t.local_outfile, t.remote_outfile, cache=False)

        # Submit the task
        q.submit(t)
        print(f"Submitted task {mechanism_labels}, command='{t.command}'")

    print("Waiting for tasks to complete...")
    while not q.empty():

        # Task ready?
        t = q.wait(5)
        if not t:
            continue

        print('Task', t.mechanism, 'complete')
        print( 'Result code', t.result)
        print(' Input transfer time:', hms(to_secs(t.send_input_finish - t.send_input_start)))
        print(' Execution time:', hms(to_secs(t.execute_cmd_finish - t.execute_cmd_start)))
        print(' Output transfer time:', hms(to_secs(t.receive_output_finish - t.receive_output_start)))

        if t.return_status != 0:
            print(t.output)
            print('Return status:', t.return_status)
            sys.exit(1)
        
        concept = load_pickle(t.local_outfile)
        print('Partial', t.local_outfile)
        print(concept)

        print('Writing final concept')
#        print(concept)          
        os.rename(t.local_outfile, t.result_file)

    print("Done")
    print("Total execution time: {}".format(hms(time() - start_time)))


if __name__ == '__main__':

    state = (0,) * 20  # TODO: pull from experiment
    elements = list(range(20))
    
    def mechanisms_for_order(elements, n):
        return pyphi.utils.combs(elements, n).tolist()

    fourth = mechanisms_for_order(elements, 4)
    random.shuffle(fourth)

    mechanisms = itertools.chain(
        mechanisms_for_order(elements, 1),
        mechanisms_for_order(elements, 2),
        mechanisms_for_order(elements, 3),
        fourth
    )
    
    # Already has a saved network file
    experiment = Experiment('largepyr', '2.1', None, state)
    port = 10006

    with WorkerFactory(experiment) as factory:
        start_master(experiment, mechanisms, state, port)

