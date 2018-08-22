#!/usr/bin/env cctools_python
# CCTOOLS_PYTHON_VERSION 2.7 2.6

# Copyright (c) 2010- The University of Notre Dame.
# This software is distributed under the GNU General Public License.
# See the file COPYING for details.

from work_queue import *


import os
import sys
import pickle
import pyphi
from time import time

# Name for the project (for catalog server)
PROJECT_NAME = 'invariants'
# It seems like we have to use ports > 10000 on HTCondor
PORT = 10001

# To start the master:
#    python master.py 
# 
# To start the worker:
#    work_queue_worker -N PROJECT_NAME  (local)
# or
#    condor_submit_worker -N PROJECT_NAME 10   (10 distributed workers)


def to_secs(mcs):
    """Convert microseconds to seconds."""
    return "{:.2f}".format(mcs / (10 ** 6))


def hms(sec_elapsed):
    """Convert seconds to hours-minutes-seconds."""
    h = int(sec_elapsed / (60 * 60))
    m = int((sec_elapsed % (60 * 60)) / 60)
    s = sec_elapsed % 60
    return "{}:{:>02}:{:>02.0f}".format(h, m, s)


def outfile(mechanism):
    return "{}.out".format(mechanism_to_str(mechanism))


def mechanism_to_str(mechanism):
    return ','.join(str(n) for n in mechanism)


if __name__ == '__main__':
    
    start_time = time()
    # network = pyphi.examples.basic_network()
    # network_pickle = 'basic.pickle'
    # with open(network_pickle, 'wb') as f:
    #     pickle.dump(network, f)

    network_pickle = 'largepyr_1.0_alloff/largepyr_1.0_alloff_network.pickle'
    state = (0,) * 20

    input_files = [
        'miniconda.tar.gz',
        'worker.sh',
        'worker.py',
        network_pickle,
     ]
    
    for filename in input_files:
        if not os.path.exists(filename):
            print(f'Input file {filename} not found')
            sys.exit(1)

    try:
        q = WorkQueue(PORT)
    except:
        print("Instantiation of Work Queue failed!")
        sys.exit(1)
    
    # Enable debug logging
        #cctools_debug_flags_set("all")

    # Identify our master via a catalog server
    # so we can past `-N PROJECT_NAME` to condor_submit_worker
    q.specify_master_mode(WORK_QUEUE_MASTER_MODE_CATALOG)
    q.specify_name(PROJECT_NAME)
    
    # TODO: enable password file
    q.specify_password_file('password_file')

    print("Listening on port %d..." % q.port)

    for node in range(20):
        mechanism = (node,)

        command = "sh worker.sh {} {} {} {}".format(
            network_pickle, 
            mechanism_to_str(state),
            mechanism_to_str(mechanism),
            outfile(mechanism))

        t = Task(command)
        t.mechanism = mechanism

        # Note that when specifying a file, we have to name its local name
        # (e.g. gzip_path), and its remote name (e.g. "gzip"). These are
        # usually the same.
        for filename in input_files:
            t.specify_input_file(filename, filename, cache=True)

        # Output files are typically not cached
        t.specify_output_file(outfile(mechanism), outfile(mechanism), cache=False)

        # Submit the task
        taskid = q.submit(t)
        print("Submitted task (id# %d): %s" % (taskid, t.command))

    print("Waiting for tasks to complete...")
    while not q.empty():

        # Task ready?
        t = q.wait(5)
        if not t:
            continue

        print('Task', t.mechanism, 'complete')
        print(' Input transfer time:', to_secs(t.send_input_finish - t.send_input_start))
        print(' Execution time:', to_secs(t.execute_cmd_finish - t.execute_cmd_start))
        print(' Output transfer time:', to_secs(t.receive_output_finish - t.receive_output_start))

        with open(outfile(t.mechanism), 'rb') as f:
            concept = pickle.load(f)
            print('Result', concept)

        if t.return_status != 0:
            print(t.output)
            print('ERROR:', t.return_status)
            sys.exit(1)

    print("Done")
    print("Total execution time: {}".format(hms(time() - start_time)))
