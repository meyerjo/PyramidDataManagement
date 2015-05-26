#!/bin/bash

# SCREENS_RUNNING=`sudo -u aclib screen -ls | grep aclib`
# if [ $? -eq 0 ]; then
#     >&2 echo "An instance of aclib is already running."
#     >&2 echo $SCREENS_RUNNING
#     >&2 echo "To reattach to the experiment run vagrant ssh"
#     >&2 echo "Aborting provisioning"
#     exit 1
# fi

echo "#############################"
echo "# Executing install scripts #"
echo "#############################"

apt-get update
apt-get install -y default-jre ruby screen

# Disable password authentication
sed -i.bak -r -e 's/(PasswordAuthentication|ChallengeResponseAuthentication|UsePAM) yes/\1 no/g' /etc/ssh/sshd_config
service sshd restart

sudo -u aclib /vagrant/aclib.sh
