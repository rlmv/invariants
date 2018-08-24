

## Installation

To instal Python and Work Queue on the submit server, run the following:

    git clone https://github.com/rlmv/invariants.git
    cd invariants
    sh ./install.sh

## Experiments

Each network of interest has a directory that holds a pickle of the network, as well as all computed concepts. See `largepyr_2.1_chtc_test.py` for an example of how to initialize an experiment. Better yet, run it!

*Do not* add pickels of networks, subsystems, etc. to the repository - they are too large, and will live in the repository forever. Instead, just add scripts to generate the networks.

## Examples

`master.py`, `test.py` and `test_factory.py` show some examples of how to use the code.

Note that if you are doing a long-running computation, and need to logout with the master and factory still running, you should use `nohup`. For example:

     nohup python master.py &

This starts the master process in the background. You can logout and it will continue running. To see processes running under `nohup` use:

     ps x
   
