#! /bin/bash

echo "####################"
echo "# Setting up AClib #"
echo "####################"
IGNORE_ERROR=true
SILENT=/dev/null

SCRIPT_DIR=/vagrant
ACLIB_DIR=/vagrant/aclib

mkdir $ACLIB_DIR || $IGNORE_ERROR
cd $ACLIB_DIR/..

# Download version if newer
wget -N -nv http://www.aclib.net/data/aclib.tar.gz
# Extract files if they are newer (Files that are deleted may remain in the machine)
tar xzkf aclib.tar.gz 2> /dev/null

ln -s $SCRIPT_DIR/run_aclib.py $ACLIB_DIR/src/run_aclib.py


echo "#######################"
echo "# Starting experiment #"
echo "#######################"

grep  "\"debug\"\s*:\s*true" < /vagrant/runconfig.json
if [ $? -eq 0 ]; then
    python -m pdb $ACLIB_DIR/src/run_aclib.py $SCRIPT_DIR/runconfig.json
else
    screen -d -m $SCRIPT_DIR/run_aclib_helper.sh $ACLIB_DIR/src/run_aclib.py $SCRIPT_DIR/runconfig.json
fi
echo "##################################"
echo "# Experiment started.            #"
echo "# Run vagrant ssh to reattach.   #"
echo "##################################"
