#! /bin/bash

echo "####################"
echo "# Setting up AClib #"
echo "####################"
IGNORE_ERROR=true
SILENT=/dev/null

SCRIPT_DIR=/vagrant
WORKING_DIR=`pwd`/my_work_dir
ACLIB_DIR=/vagrant/aclib

mkdir $ACLIB_DIR || $IGNORE_ERROR
cd $ACLIB_DIR/..

# Download version if newer
wget -N -nv http://www.aclib.net/data/aclib.tar.gz
# Extract files if they are newer (Files that are deleted may remain in the machine)
tar xzkf aclib.tar.gz 2> /dev/null

mkdir $WORKING_DIR || $IGNORE_ERROR
cd $WORKING_DIR
cp $SCRIPT_DIR/run_aclib.py $WORKING_DIR/run_aclib.py

echo "#######################"
echo "# Starting experiment #"
echo "#######################"

grep  "\"debug\"\s*:\s*true" < runconfig.json
if [ $? -eq 0 ] then
    yes | $WORKING_DIR/run_aclib.py $SCRIPT_DIR/runconfig.json
else
    screen -d -m $SCRIPT_DIR/run_aclib_helper.sh $WORKING_DIR/run_aclib.py $SCRIPT_DIR/runconfig.json
fi
echo "##################################"
echo "# Experiment started.            #"
echo "# Run vagrant ssh to reattach.   #"
echo "##################################"
