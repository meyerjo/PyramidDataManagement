#! /bin/bash

echo "####################"
echo "# Setting up AClib #"
echo "####################"
IGNORE_ERROR=true
SILENT=/dev/null

SCRIPT_DIR=/vagrant/accloud
ACLIB_DIR=/vagrant/aclib
EXP_DIR=/vagrant/experiment

# Download version if newer
wget -N -nv -P /tmp http://www.aclib.net/data/aclib.tar.gz 
# Extract files if they are newer (Files that are deleted may remain in the machine)
tar xzkf /tmp/aclib.tar.gz -C $ACLIB_DIR/.. 2> $SILENT
cp -rv $SCRIPT_DIR/aclib/* $ACLIB_DIR/

echo "#######################"
echo "# Starting experiment #"
echo "#######################"

cd /vagrant

grep  "\"debug\"\s*:\s*true" < $EXP_DIR/runconfig.json
if [ $? -eq 0 ]; then
    screen -d -m python -m pdb $ACLIB_DIR/src/run_aclib.py $EXP_DIR/runconfig.json
else
    screen -d -m -L sh -c '$ACLIB_DIR/src/run_aclib.py $EXP_DIR/runconfig.json; sudo poweroff'
fi
echo "##################################"
echo "# Experiment started.            #"
echo "# Run vagrant ssh to reattach.   #"
echo "##################################"
