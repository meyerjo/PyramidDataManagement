# -*- mode: ruby -*-
# vi: set ft=ruby :

require 'json'
require 'fileutils'

# Require needed vagrant plugins
required_plugins = %w( vagrant-azure vagrant-rsync-pull )
required_plugins.each do |plugin|
    if not Vagrant.has_plugin? plugin
        raise Vagrant::Errors::PluginNotInstalled, name: plugin
    end
end

# Load ACcloud config files
global_config_file = '../credentials.json'
local_config_file = 'runconfig.json'
cwd = File.dirname(File.absolute_path(__FILE__))

# Parse config files
begin
local_config = JSON.parse(File.read(local_config_file))
global_config = JSON.parse(File.read(global_config_file))
ac_config = local_config.merge(global_config)

# If config file in experiment box does not exist, copy default file
rescue Errno::ENOENT => e
    if not File.exists?(global_config_file)
        FileUtils.cp(File.join(cwd, File.basename(global_config_file)), File.join(Dir.pwd, global_config_file))
    end
    if not File.exists?(local_config_file)
        FileUtils.cp(File.join(cwd, local_config_file), File.join(Dir.pwd, local_config_file))
    end
    raise Vagrant::Errors::ConfigInvalid, errors: "#{e.message} - Template config file has been inserted"
end


Vagrant.configure(2) do |config|

    config.ssh.username = ac_config['vm']['user']

    if ac_config.has_key?('azure') and ac_config['machine'].has_key?('azure')
        config.vm.provider :azure do |azure, overwrite|

            # Subscription id and Management certificate for authentication with the azure service
            azure.subscription_id = ac_config['azure']['subscription_id']
            azure.mgmt_certificate = ac_config['azure']['certificate']
            azure.mgmt_endpoint = 'https://management.core.windows.net'
            
            # Specifics about the vm image and configuration
            azure.vm_image = "b39f27a8b8c64d52b05eac6a62ebad85__Ubuntu-14_04_2_LTS-amd64-server-20150309-en-us-30GB"
            azure.vm_size = ac_config['machine']['azure']['category']

            # Hostname and location of the machine
            azure.vm_name = ac_config['name']
            azure.vm_location = ac_config['machine']['azure']['location']
            azure.storage_acct_name  = 'accloud'

            # VM login username and password according to config
            azure.vm_user = ac_config['vm']['user']
            azure.vm_password = ac_config['vm']['password']
            overwrite.ssh.password = ac_config['vm']['password']
        end
    end

    if ac_config.has_key?('aws') and ac_config['machine'].has_key?('aws')
        config.vm.provider :aws do |aws, overwrite|

            # Instance settings
            aws.instance_type = ac_config['machine']['aws']['category']
            aws.region = ac_config['machine']['aws']['location']
            aws.tags = {
                'Name' => ac_config['name']
            }

            # Image ID ubuntu/images/hvm-ssd/ubuntu-trusty-14.04-amd64-server-20150325
            aws.ami = "ami-d05e75b8"

            # Credential information (User needs ec2 permission role)
            aws.access_key_id = ac_config['aws']['access_key_id']
            aws.secret_access_key = ac_config['aws']['secret_access_key']
            aws.user_data = "#cloud-config\nsystem_info:\n  default_user:\n    name: #{ac_config['vm']['user']}"
            aws.security_groups = "launch-wizard-1"

            # Key from keypairs has to be used
            overwrite.ssh.private_key_path = ac_config['aws']['keypair']
            aws.keypair_name = File.basename(ac_config['aws']['keypair'], '.pem')

            # Bug in vagrant-aws provisioning
            # https://github.com/mitchellh/vagrant-aws/issues/357#issuecomment-95677595
            overwrite.nfs.functional = false
        end
    end

    # Folder of the experiment box
    config.vm.synced_folder ".", "/vagrant/experiment",
        type: "rsync",
        rsync__exclude: ["results", "aclib"]

    # Custom modifications of aclib in the experiment box
    config.vm.synced_folder "aclib", "/vagrant/aclib",
        type: "rsync",
        owner: ac_config['vm']['user'],
        create: true

    # Folder containing the working directories of the experiments.
    # Is only synced back
    config.vm.synced_folder "results", "/vagrant/results",
        type: "rsync_pull",
        rsync_pull__args: ["--verbose",
            "--recursive", "--links", "--times",
            "--compress", "--ignore-existing"],
        create: true

    # Folder of the ac-cloud box containing all the helper scripts
    config.vm.synced_folder cwd, "/vagrant/accloud",
        type: "rsync"

    # Bashrc to automatically attach to the screen
    config.vm.provision "file",
        source: File.join(cwd, ".bashrc"),
        destination: File.join("/home", ac_config['vm']['user'], ".bashrc")

    # Bootstrap script setting up the packages, and starting the aclib-bootstrap
    config.vm.provision "shell", inline: "/vagrant/accloud/install.sh"

    # Define and set up several machines
    if ac_config['machine']['multi-machine'] > 1
        for i in 1..ac_config['machine']['multi-machine']
            config.vm.define "#{ac_config['name']}-#{i}"
        end
    end
end
