set -e 

# Unpack and run the python worker

tar -xf miniconda.tar.gz
./miniconda/bin/python worker.py $@