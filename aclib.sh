#! /bin/bash

echo "####################"
echo "# Setting up AClib #"
echo "####################"
IGNORE_ERROR=true
SILENT=/dev/null

WORKING_DIR=my_work_dir

cd /vagrant
mkdir aclib || $IGNORE_ERROR

# Download version if newer
wget -N -nv http://www.aclib.net/data/aclib.tar.gz
# Extract files if they are newer (Files that are deleted may remain in the machine)
tar xzkf aclib.tar.gz 2> /dev/null

mkdir $WORKING_DIR || $IGNORE_ERROR
cd $WORKING_DIR

yes | python /vagrant/aclib/src/install_scenario.py -s CSSC_regressiontests_spear

echo "#######################"
echo "# Starting experiment #"
echo "#######################"

python run_aclib.py runconfig.json

echo "##################################"
echo "# Experiment started.            #"
echo "# Run vagrant ssh to reattach.   #"
echo "##################################"
