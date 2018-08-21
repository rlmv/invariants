#!/usr/bin/env bash

set -e
set -x

# VERSION=3.6.3
# PYTHON_URL=https://www.python.org/ftp/python/$VERSION/Python-$VERSION.tgz
# PYTHON_TARBALL=Python-$VERSION.tgz
# PYTHON_SOURCE=Python-$VERSION
# PYTHON_BUILD=$(pwd)/python
# OUT=python.tar.gz

# curl $PYTHON_URL -o $PYTHON_TARBALL

# mkdir $PYTHON_BUILD
# tar -xzvf $PYTHON_TARBALL

# cd $PYTHON_SOURCE
# ./configure --prefix=$PYTHON_BUILD
# make
# make install
# cd ..

# echo "export PATH=~/python/bin:$PATH" >> ~/.bashrc
# echo "alias python=python3" >> ~/.bashrc
# echo "alias pip=pip3" >> ~/.bashrc
# source ~/.bashrc

# pip3 install -v git+https://github.com/wmayner/pyphi@develop
# pip3 install -r requirements.txt

# # Create tarball of distribution
# tar -czvf $OUT python

# # Cleanup
# rm -rf $PYTHON_SOURCE $PYTHON_TARBALL $PYTHON_BUILD

MINICONDA_INSTALLER=miniconda.sh
MINICONDA_BUILD=$HOME/miniconda
wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O $MINICONDA_INSTALLER
chmod +x $MINICONDA_INSTALLER
./$MINICONDA_INSTALLER -p $MINICONDA_BUILD

# TODO: ensure miniconda is added to PATH

pip install -r requirements.txt

tar -cvf miniconda.tar.gz $MINICONDA_BUILD

# Install CC Tools (WorkQueue)
CCTOOLS_NAME=cctools-7.0.3-source
wget http://ccl.cse.nd.edu/software/files/${CCTOOLS_NAME}.tar.gz
tar zxvf ${CCTOOLS_NAME}.tar.gz
cd ${CCTOOLS_NAME}
./configure --with-python-path no --with-perl-path no --with-globus-path no --with-python3-path $MINICONDA_BUILD
make
make install

echo "export PATH=${HOME}/cctools/bin:$PATH" >> ~/.bashrc
source ~/.bashrc