#!/usr/bin/env cctools_python
# CCTOOLS_PYTHON_VERSION 2.7 2.6

# Copyright (c) 2010- The University of Notre Dame.
# This software is distributed under the GNU General Public License.
# See the file COPYING for details.

from work_queue import *

import random
import itertools
import os
import sys
import pickle
import pyphi
from time import time
from utils import Experiment


# Name for the project (for catalog server)
PROJECT_NAME = 'invariants'
# We have to use ports > 10000 on HTCondor
PORT = 10002
PASSWORD_FILE = 'password_file'
LOG_FILE = f'{PROJECT_NAME}.log'

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


def load_pickle(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)


if __name__ == '__main__':

    pyphi.config.REPR_VERBOSITY = 1
    
    start_time = time()
    # network = pyphi.examples.basic_network()
    # network_pickle = 'basic.pickle'
    # with open(network_pickle, 'wb') as f:
    #     pickle.dump(network, f)

    state = (0,) * 20
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

    experiment = Experiment('largepyr', '2.1', None, state)
    network = load_pickle(experiment.network_file)

    def outfile(mechanism):
        return "{}.pickle".format(mechanism_to_labels(network, mechanism))

    def local_outfile(mechanism):
        return os.path.join(experiment.directory, outfile(mechanism))

    input_files = [
        'miniconda.tar.gz',
        'worker.sh',
        'worker.py',
        experiment.network_file
     ]
    
    for filename in input_files:
        if not os.path.exists(filename):
            print(f'Input file {filename} not found')
            sys.exit(1)

    q = WorkQueue(PORT)
    
    # Enable debug logging
    # cctools_debug_flags_set("all")
    q.specify_log(LOG_FILE)

    # Identify our master via a catalog server
    # so we can pass `-N PROJECT_NAME` to condor_submit_worker
    q.specify_master_mode(WORK_QUEUE_MASTER_MODE_CATALOG)
    q.specify_name(PROJECT_NAME)
    
    # Enable password file
    # TODO: make this optional?
    if not q.specify_password_file(PASSWORD_FILE):
        raise Exception('Failed to specify password file')

    print("Listening on port %d..." % q.port)

    for mechanism in mechanisms:
        mechanism = tuple(mechanism)

        remote_outfile = outfile(mechanism)

        if os.path.exists(local_outfile(mechanism)):
            print(local_outfile(mechanism), 'exists. Skipping mechanism', mechanism_to_str(mechanism))
            continue

        command = "sh worker.sh {} {} {} {}".format(
            experiment.network_file,
            mechanism_to_str(state),
            mechanism_to_str(mechanism),
            remote_outfile)

        t = Task(command)
        t.mechanism = mechanism

        # Note that when specifying a file, we have to name its local name
        # (e.g. gzip_path), and its remote name (e.g. "gzip"). These are
        # usually the same.
        for filename in input_files:
            t.specify_input_file(filename, filename, cache=True)

        # Output files are typically not cached
        t.specify_output_file(local_outfile(mechanism), remote_outfile, cache=False)

        # Submit the task
        taskid = q.submit(t)
        print(f"Submitted task {mechanism}, id={t.id}, command='{command}'")

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

        with open(local_outfile(t.mechanism), 'rb') as f:
            concept = pickle.load(f)
            print(concept)

    print("Done")
    print("Total execution time: {}".format(hms(time() - start_time)))
