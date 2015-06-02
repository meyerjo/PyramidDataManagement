# -*- mode: ruby -*-
# vi: set ft=ruby :

require 'json'

local_config = JSON.parse(File.read('runconfig.json'))
global_config = JSON.parse(File.read('../credentials.json'))
ac_config = local_config.merge(global_config)

vm_user = ac_config['vm']['user']
vm_pass = ac_config['vm']['password']


Vagrant.configure(2) do |config|
  # All Vagrant configuration is done here. The most common configuration
  # options are documented and commented below. For a complete reference,
  # please see the online documentation at vagrantup.com.

    config.vm.box = 'https://github.com/MSOpenTech/vagrant-azure/raw/master/dummy.box'

    config.vm.provider :azure do |azure|
        azure.subscription_id = ac_config['azure']['subscription_id']
        azure.mgmt_certificate = ac_config['azure']['certificate']
        azure.vm_image = "b39f27a8b8c64d52b05eac6a62ebad85__Ubuntu-14_04_2_LTS-amd64-server-20150309-en-us-30GB"
        azure.vm_size = ac_config['machine']['azure_category']
        azure.mgmt_endpoint = 'https://management.core.windows.net'
        azure.vm_name = ac_config['experiment']['name']
        azure.vm_location = ac_config['machine']['location']
        # Default password will be disabled after random key insertion
        azure.vm_user = vm_user
        azure.vm_password = vm_pass
    end

    config.vm.provider :virtualbox do |v|
        v.memory = ac_config['machine']['memory']
        v.cpus = ac_config['machine']['cores']
    end

    config.ssh.username = vm_user
    config.ssh.password = vm_pass
    config.vm.synced_folder "target_algorithms/", "/vagrant/aclib/target_algorithms", owner: vm_user
    config.vm.synced_folder "instances/", "/vagrant/aclib/instances", owner: vm_user
    config.vm.synced_folder "scenarios/", "/vagrant/aclib/scenarios", owner: vm_user
    config.vm.provision "file", source: ".bashrc", destination: "/home/#{vm_user}/.bashrc"
    config.vm.provision "shell", path: "install.sh"

    if ac_config['machine']['multi-machine'] > 1
        for i in 1..ac_config['machine']['multi-machine']
            config.vm.define "#{ac_config['experiment']['name']}-#{i}"
        end
    end
end
