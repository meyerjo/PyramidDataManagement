#!/bin/bash

SCREENS_RUNNING=`sudo -u aclib screen -ls | grep -E 'There (is a|are) screens? on:'`
if [ $? -eq 0 ]; then
    >&2 echo "An instance of aclib is already running."
    >&2 echo $SCREENS_RUNNING
    >&2 echo "To reattach to the experiment run vagrant ssh"
    >&2 echo "and eventually stop the experiment"
    >&2 echo "Aborting provisioning"
    exit 1
fi

echo "#############################"
echo "# Executing install scripts #"
echo "#############################"

# Update if last update is older than 1 day
# Probs to http://askubuntu.com/questions/487606/bash-update-apt-get-only-if-apt-cache-is-older-than-10-minutes
if [ "$[$(date +%s) - $(stat -c %Z /var/lib/apt/periodic/update-success-stamp)]" -ge 86400 ]; then
    apt-get -qq update
fi
apt-get -qq install -y default-jre ruby screen python-numpy

# Disable password authentication
sed -i.bak -r -e 's/(PasswordAuthentication|ChallengeResponseAuthentication) yes/\1 no/g' /etc/ssh/sshd_config
service ssh restart

sudo -u aclib /vagrant/accloud/aclib.sh
