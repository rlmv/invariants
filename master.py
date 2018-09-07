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
from utils import Experiment, load_pickle, dump_pickle, PartialConcept

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
                '--memory', '8192',
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


class ConceptTask(Task):

    def __init__(self, experiment, mechanism, timeout):
        self.experiment = experiment
        self.mechanism = mechanism
        self.timeout = timeout

        # Unique ID for this task
        # Work Queue tasks also have an `id`, but this is not generated
        # until the task is submitted
        self.uuid = uuid4()
        
        super().__init__(self.command)

    @property
    def command(self):
        return "sh worker.sh {} {} {} {} {}".format(
                self.experiment.network_file,
                mechanism_to_str(self.experiment.state),
                self.infile,
                self.outfile,
                self.timeout)

    @property
    def infile(self):
        return f'{self.outfile}.input'

    @property
    def result_file(self):
        return f'{self.experiment.directory}/{mechanism_to_labels(self.experiment.network, self.mechanism)}.pickle'

    @property
    def partial_result_file(self):
        return f'{self.result_file}.part'

    @property
    def outfile(self):
        return f'{self.result_file}.part:{self.uuid}'

    def merge_results(self):
        # If the cumulative a master outfile does not exist, make the output
        # of this task the 
        if not os.path.exists(self.partial_result_file):
            print(f'Promoting {self.outfile} to {self.partial_result_file}')
            os.rename(self.outfile, self.partial_result_file)
            return load_pickle(self.partial_result_file), self.partial_result_file

        this_result = load_pickle(self.outfile)
        print(f'Merging {self.outfile} into {self.partial_result_file}')

        running_result = load_pickle(self.partial_result_file)
        running_result.merge_partial(this_result)
        dump_pickle(self.partial_result_file, running_result)
        os.remove(self.outfile)

        return running_result, self.partial_result_file


def partial_child_task(child, experiment, input_files, timeout):
    mechanism = child.mechanism
    t = ConceptTask(experiment, mechanism, timeout)
    dump_pickle(t.infile, child)

    t.specify_input_file(t.infile, t.infile, cache=False)

    for filename in input_files:
        t.specify_input_file(filename, filename, cache=True)
    
    t.specify_output_file(t.outfile, t.outfile, cache=False)
    
    # Increase the priority so we can finish up all the parts before starting
    # new concepts
    t.specify_priority(1)

    return t


def start_master(experiment, mechanisms, port=10001, timeout=3600, n_divisions=10):
    print(f'Starting {experiment.project_name}...')
    start_time = time()

    input_files = [
        'miniconda.tar.gz',
        'worker.sh',
        'worker.py',
        'utils.py',
        'pyphi_config.yml',
        experiment.network_file
     ]
    
    for filename in input_files:
        if not os.path.exists(filename):
            print(f'Input file {filename} not found')
            sys.exit(1)

    q = WorkQueue(port)
    
    # Enable debug logging
#    cctools_debug_flags_set("wq")
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
        mechanism_labels = mechanism_to_labels(experiment.network, mechanism)

        t = ConceptTask(experiment, mechanism, timeout)

        if os.path.exists(t.result_file):
            print(mechanism_labels, 'complete. Skipping.')
        
        elif os.path.exists(t.partial_result_file):
            print(mechanism_labels, 'partial result found; continuing...')
            partial_concept = load_pickle(t.partial_result_file)
            for i, child in enumerate(partial_concept.divide(n_divisions)):
                child_t = partial_child_task(child, experiment, input_files, timeout)
                # Submit the task
                q.submit(child_t)
                print(f"Submitted part {i} of {mechanism_labels}, command='{child_t.command}'")
        else:
            partial_concept = PartialConcept(mechanism)
            t = partial_child_task(partial_concept, experiment, input_files, timeout)
            t.specify_priority(0)

            # Submit the task
            q.submit(t)
            print(f"Submitted task {mechanism_labels}, command='{t.command}'")

    print("Waiting for tasks to complete...", flush=True)
    while not q.empty():

        # Task ready?
        t = q.wait(5)
        if not t:
            continue
        
        print()
        print('Got result', t.outfile)
        print( 'Result code', t.result)
        print(' Input transfer time:', hms(to_secs(t.send_input_finish - t.send_input_start)))
        print(' Execution time:', hms(to_secs(t.execute_cmd_finish - t.execute_cmd_start)))
        print(' Output transfer time:', hms(to_secs(t.receive_output_finish - t.receive_output_start)))

        if t.return_status != 0:
            print(t.output)
            print('Return status:', t.return_status)
            sys.exit(1)
            
        partial_concept = load_pickle(t.outfile)

        if partial_concept.unfinished:
            print('Timed out. Submitting smaller jobs...')
            for i, child in enumerate(partial_concept.divide(n_divisions)):
                
                child_t = partial_child_task(child, experiment, input_files, timeout)
                # Submit the task
                q.submit(child_t)
                print(f"Submitted child {i}, command='{child_t.command}'")

        # Combine this partial result with any other partial results
        partial_concept, partial_filename = t.merge_results()
        print('Updated partial concept to be')
        print(partial_concept.concept, flush=True)

        # Did this piece complete the whole?
        if not partial_concept.unfinished:
            print('Writing final concept')
            dump_pickle(t.result_file, partial_concept.concept)
            os.remove(partial_filename)
            
        os.remove(t.infile)

    print("Done")
    print("Total execution time: {}".format(hms(time() - start_time)))

