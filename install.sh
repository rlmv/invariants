#!/usr/bin/env bash

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


# Install Miniconda
MINICONDA_INSTALLER=miniconda.sh
MINICONDA_DIRNAME=miniconda
MINICONDA_BUILD=$HOME/$MINICONDA_DIRNAME
MINICONDA_TARBALL=miniconda.tar.gz
wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O $MINICONDA_INSTALLER
chmod +x $MINICONDA_INSTALLER
./$MINICONDA_INSTALLER -b -p $MINICONDA_BUILD

rm $MINICONDA_INSTALLER

# Install requirements into Miniconda
$MINICONDA_BUILD/bin/pip install -r requirements.txt

# Make a tarball of Miniconda
CURRENT=`pwd`
cd $HOME && tar -cvf $MINICONDA_TARBALL $MINICONDA_DIRNAME
mv $MINICONDA_TARBALL $CURRENT
cd $CURRENT

# Install CC Tools (WorkQueue)
CCTOOLS_NAME=cctools-7.0.3-source
CCTOOLS_BUILD=$HOME/cctools
wget http://ccl.cse.nd.edu/software/files/$CCTOOLS_NAME.tar.gz
tar zxvf $CCTOOLS_NAME.tar.gz
cd $CCTOOLS_NAME
./configure --with-python-path no --with-perl-path no --with-globus-path no --with-python3-path $MINICONDA_BUILD
make
make install
cd $CURRENT

rm $CCTOOLS_NAME.tar.gz

# Modify paths
printf "export PATH=\"%s/bin:\$PATH\"\\n" $MINICONDA_BUILD  >> ~/.bashrc
printf "export PATH=\"%s/bin:\$PATH\"\\n" $CCTOOLS_BUILD  >> ~/.bashrc
printf "export PYTHONPATH=\"%s/lib/python3.6/site-packages/\"\\n" $CCTOOLS_BUILD  >> ~/.bashrc
source ~/.bashrc
