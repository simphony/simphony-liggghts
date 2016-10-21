#!/bin/bash
set -e

if [ -z "$PYTHON_LIB_DIR" ]; then echo "Set PYTHON_LIB_DIR variable to location of where LIGGGHTS shared library and liggghts.py should be installed (currently using default)"; fi

PYTHON_LIB_DIR=${PYTHON_LIB_DIR:-$VIRTUAL_ENV/lib/python2.7/site-packages/}

# Create folder for liggghts executable storage
mkdir -p $HOME/.local/bin
export PATH=$PATH:$HOME/.local/bin

echo "Installing python LIGGGHTS wrapper to '$PYTHON_LIB_DIR'"


echo "Checking out the most recent release of liggghts - 3.4.0 from 17 May 2016"
git clone --branch 3.4.0 --depth 1 git://github.com/CFDEMproject/LIGGGHTS-PUBLIC.git myliggghts

pushd myliggghts
# Apply our patch to rename namespaces and lammps references with liggghts ones
git apply ../liggghts.patch
echo "Patched liggghts source code"
popd

echo "Building LIGGGHTS executable"
pushd myliggghts/src
make -j 2 fedora
ln -s lgt_fedora liggghts
cp lgt_fedora $HOME/.local/bin/liggghts

echo "Making shared library for LIGGGHTS python wrapper"
make makeshlib
make  -j 2 -f Makefile.shlib fedora_fpic
ln -s libliggghts_fedora_fpic.so libliggghts.so
popd


echo "Installing LIGGGHTS python wrapper"
pushd myliggghts/python
# The install script expects `liggghts.py` name.
cp lammps.py liggghts.py
# Make sure the path is in LD_LIBRARY_PATH
export LD_LIBRARY_PATH=$PYTHON_LIB_DIR:$LD_LIBRARY_PATH
python install.py $PYTHON_LIB_DIR $PYTHON_LIB_DIR
popd

python check_liggghts_python.py

echo "Add $PYTHON_LIB_DIR to your LD_LIBRARY_PATH in case of failure"