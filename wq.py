#!/usr/bin/env cctools_python
# CCTOOLS_PYTHON_VERSION 2.7 2.6

# Copyright (c) 2010- The University of Notre Dame.
# This software is distributed under the GNU General Public License.
# See the file COPYING for details.

from work_queue import *

import os
import sys

PROJECT_NAME = 'invariants'
PORT = 10001

# Main program
if __name__ == '__main__':

    miniconda = os.path.abspath('miniconda.tar.gz')
    if not os.path.exists(miniconda):
        print('Miniconda not found')
        sys.exit(1)

    # It seems like we have to use ports > 10000 on HTCondor
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

    for i in range(1, 2):
        outfile = "{}.out".format(i)

        command = "sh worker.sh {}".format(i)
        t = Task(command)
        t.extra = 'bo'
        t.mechanism = i

        # Note that when specifying a file, we have to name its local name
        # (e.g. gzip_path), and its remote name (e.g. "gzip"). Unlike the
        # following line, more often than not these are the same.
        t.specify_input_file('worker.sh', 'worker.sh', cache=True)
        t.specify_input_file('worker.py', 'worker.py', cache=True)
        t.specify_input_file(miniconda, "miniconda.tar.gz", cache=True)

        # files to be compressed are different across all tasks, so we do not
        # cache them. This is, of course, application specific. Sometimes you may
        # want to cache an output file if is the input of a later task.
        t.specify_output_file(outfile, outfile, cache=False)

        # Once all files has been specified, we are ready to submit the task to the queue.
        taskid = q.submit(t)
        print("submitted task (id# %d): %s" % (taskid, t.command))

    print("waiting for tasks to complete...")
    while not q.empty():
        t = q.wait(5)
        
        if t:
            assert t.extra == 'bo'

            print("task (id# %d) complete: %s (return code %d)" % (t.id, t.command, t.return_status))
            if t.return_status != 0:
                raise ValueError(
                    'return_status: %s\noutput: %s', t.return_status, t.output)

    print("Done")
    sys.exit(0)
