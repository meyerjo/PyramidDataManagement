# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!

Vagrant.configure(2) do |config|
  # All Vagrant configuration is done here. The most common configuration
  # options are documented and commented below. For a complete reference,
  # please see the online documentation at vagrantup.com.

    config.vm.box = 'https://github.com/MSOpenTech/vagrant-azure/raw/master/dummy.box'

    config.vm.provider :azure do |azure|
        azure.subscription_id = "daa4b9a5-0ee0-4c47-9136-ad1e7a22e4a7"
        azure.mgmt_certificate = 'daa4b9a5-0ee0-4c47-9136-ad1e7a22e4a7.pem'
        azure.vm_image = "b39f27a8b8c64d52b05eac6a62ebad85__Ubuntu-14_04_2_LTS-amd64-server-20150309-en-us-30GB"
        azure.vm_size = "Small"
        azure.mgmt_endpoint = 'https://management.core.windows.net'
        azure.vm_name = 'standard-aclib'
        azure.vm_location = 'West Europe'
        # Default password will be disabled after random key insertion
        azure.vm_user = 'aclib'
        azure.vm_password = '4clib!'
    end

    config.vm.provider :virtualbox do |v|
        v.memory = 1024
        v.cpus = 2
    end

    config.ssh.username = 'aclib'
    config.ssh.password = '4clib!'
    config.vm.synced_folder "target-algorithms/", "/vagrant/aclib/target-algorithms", owner: "aclib"
    config.vm.synced_folder "instances/", "/vagrant/aclib/instances", owner: "aclib"
    config.vm.synced_folder "scenarios/", "/vagrant/aclib/scenarios", owner: "aclib"
    config.vm.provision "file", source: ".bashrc", destination: "/home/aclib/.bashrc"
    config.vm.provision "shell", path: "install.sh"
end
