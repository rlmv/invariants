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

PROJECT_NAME = 'invariants'
# It seems like we have to use ports > 10000 on HTCondor
PORT = 10001


if __name__ == '__main__':

    network = pyphi.examples.basic_network()
    network_pickle = 'basic.pickle'
    with open(network_pickle, 'wb') as f:
        pickle.dump(network, f)

    miniconda = os.path.abspath('miniconda.tar.gz')
    if not os.path.exists(miniconda):
        print('Miniconda not found')
        sys.exit(1)

    try:
        q = WorkQueue(PORT)
    except:
        print("Instantiation of Work Queue failed!")
        sys.exit(1)
    
    # Enable debug logging
#    cctools_debug_flags_set("all")

    # Identify our master via a catalog server
    # so we can past `-N PROJECT_NAME` to condor_submit_worker
    q.specify_master_mode(WORK_QUEUE_MASTER_MODE_CATALOG)
    q.specify_name(PROJECT_NAME)
    
    # TODO: enable password file
    # q.specify_password_file('password_file')

    print("Listening on port %d..." % q.port)

    def _outfile(mechanism):
        return "{}.out".format(mechanism)

    def mechanism_to_str(mechanism):
        return ','.join(str(n) for n in mechanism)

    for mechanism in pyphi.utils.powerset((0, 1), nonempty=True):
        
        outfile = _outfile(mechanism_to_str(mechanism))
        command = "sh worker.sh {} {}".format(network_pickle, mechanism_to_str(mechanism))
        t = Task(command)
        t.extra = 'bo'
        t.mechanism = mechanism

        # Note that when specifying a file, we have to name its local name
        # (e.g. gzip_path), and its remote name (e.g. "gzip"). Unlike the
        # following line, more often than not these are the same.
        t.specify_input_file('worker.sh', 'worker.sh', cache=True)
        t.specify_input_file('worker.py', 'worker.py', cache=True)
        t.specify_input_file(miniconda, "miniconda.tar.gz", cache=True)
        t.specify_input_file(network_pickle, network_pickle, cache=True)

        # files to be compressed are different across all tasks, so we do not
        # cache them. This is, of course, application specific. Sometimes you may
        # want to cache an output file if is the input of a later task.
        t.specify_output_file(outfile, outfile, cache=False)

        # Once all files has been specified, we are ready to submit the task to the queue.
        taskid = q.submit(t)
        print("Submitted task (id# %d): %s" % (taskid, t.command))

    print("Waiting for tasks to complete...")
    while not q.empty():

        # Task ready?
        t = q.wait(5)
        if not t:
            continue

        assert t.extra == 'bo'
        print('Task', t.mechanism, 'complete')
        
        def to_secs(mcs):
            """Convert microseconds to seconds."""
            return "{:.2f}".format(mcs / (10 ** 6))
        
        print(' Input transfer time:', to_secs(t.send_input_finish - t.send_input_start))
        print(' Execution time:', to_secs(t.execute_cmd_finish - t.execute_cmd_start))
        print(' Output transfer time:', to_secs(t.receive_output_finish - t.receive_output_start))

        with open(_outfile(mechanism_to_str(t.mechanism)), 'rb') as f:
            concept = pickle.load(f)
            print('Result', concept)

        if t.return_status != 0:
            print(t.output)
            print('ERROR:', t.return_status)
            sys.exit(1)

    print("Done")
    sys.exit(0)
