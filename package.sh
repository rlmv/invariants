#!/usr/bin/env bash

set -e
set -x

VERSION=3.6.3
PYTHON_URL=https://www.python.org/ftp/python/$VERSION/Python-$VERSION.tgz
PYTHON_TARBALL=Python-$VERSION.tgz
PYTHON_SOURCE=Python-$VERSION
BUILD=$(pwd)/python
OUT=python.tar.gz

curl $PYTHON_URL -o $PYTHON_TARBALL

mkdir $BUILD
tar -xzvf $PYTHON_TARBALL

cd $PYTHON_SOURCE
./configure --prefix=$BUILD
make
make install
cd ..

echo "export PATH=~/python/bin:$PATH" >> ~/.bashrc
echo "alias python=python3" >> ~/.bashrc
source ~/.bashrc

pip3 install -v git+https://github.com/wmayner/pyphi@develop

# Create tarball of distribution
tar -czvf $OUT python

# Cleanup
rm -rf $PYTHON_SOURCE $PYTHON_TARBALL $BUILD