# -*- mode: ruby -*-
# vi: set ft=ruby :

require 'json'
require 'fileutils'

required_plugins = %w( vagrant-azure vagrant-rsync-pull )
required_plugins.each do |plugin|
    if not Vagrant.has_plugin? plugin
        raise Vagrant::Errors::PluginNotInstalled, name: plugin
    end
end

global_config_file = '../credentials.json'
local_config_file = 'runconfig.json'
cwd = File.dirname(File.absolute_path(__FILE__))

begin
local_config = JSON.parse(File.read(local_config_file))
global_config = JSON.parse(File.read(global_config_file))
ac_config = local_config.merge(global_config)

rescue Errno::ENOENT => e
    if not File.exists?(global_config_file)
        FileUtils.cp(File.join(cwd, File.basename(global_config_file)), File.join(Dir.pwd, global_config_file))
    end
    if not File.exists?(local_config_file)
        FileUtils.cp(File.join(cwd, local_config_file), File.join(Dir.pwd, local_config_file))
    end
    raise Vagrant::Errors::ConfigInvalid, "Please configure the provided config files: #{e.message}"
end

vm_user = ac_config['vm']['user']
vm_pass = ac_config['vm']['password']


Vagrant.configure(2) do |config|
    config.vm.provider "azure"
    config.vm.provider "virtualbox"

    config.vm.box = 'https://github.com/MSOpenTech/vagrant-azure/raw/master/dummy.box'

    config.vm.provider :azure do |azure|
        azure.subscription_id = ac_config['azure']['subscription_id']
        azure.mgmt_certificate = File.join(File.dirname(global_config_file), ac_config['azure']['certificate'])
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
    config.vm.synced_folder "aclib", "/vagrant/aclib", owner: vm_user, create: true
    config.vm.synced_folder "results", "/vagrant/results", type: "rsync_pull",
        rsync_pull__args: ["--verbose", "--archive", "--delete", "-z"], create: true

    
    config.vm.synced_folder cwd, "/vagrant"
    config.vm.provision "file", source: "#{cwd}/.bashrc", destination: "/home/#{vm_user}/.bashrc"


    config.vm.provision "shell", inline: "/vagrant/install.sh"

    if ac_config['machine']['multi-machine'] > 1
        for i in 1..ac_config['machine']['multi-machine']
            config.vm.define "#{ac_config['experiment']['name']}-#{i}"
        end
    end
end
