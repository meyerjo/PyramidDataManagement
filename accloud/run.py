import os
import os.path as path
import shutil
import sys
import tarfile
import subprocess
import logging
import glob
import json
from config import Config


class Run(object):
    '''Representation of an ACcloud vagrant box'''
    def __init__(self, boxpath):
        self.config = Config()
        if boxpath is None:
            self.path = os.getcwd()
        else:
            self.path = boxpath

        if not path.isdir(self.path):
            os.makedirs(self.path)

        try:
            json = open(path.join(self.path, 'runconfig.json'), 'r')
            self.config.load(json)
        except IOError:
            pass

    def is_archived(self):
        archive_path = path.join(self.path, 'results.tar.gz')
        result_path = path.join(self.path, 'results')

        archive_exists = (path.isfile(archive_path)
                          and tarfile.is_tarfile(archive_path))
        results_exist = path.isdir(result_path)

        if archive_exists and not results_exist:
            return True

        if results_exist and not archive_exists:
            return False

    def create(self, **kwargs):
        if self.config.loaded_files:
            logging.critical('Experiment already initialized')
            return

        config = {
            'name': os.path.basename(self.path),
            'parallel_runs': kwargs['n_per_job'],
            'experiment': {
                'scenario': kwargs['scenario'],
                'configurator': kwargs['configurator'],
                'config_file': kwargs['config_file'],
                'seed': kwargs['seed'],
                'only_prepare': kwargs['only_validate'],
                'repetition': kwargs['n_runs'],
            },
            'machine': {
                'provider': {
                    'name': kwargs['provider'],
                    'instance': kwargs['instance']
                },
                'multi-machine': kwargs['multi_machine']
            }
        }

        if kwargs['instance']:
            config['machine']['instance'] = kwargs['instance']
        else:
            config['machine']['cores'] = kwargs['job_cores']
            config['machine']['memory'] = kwargs['job_memory']

        runconfig_file = open(path.join(self.path, 'runconfig.json'), 'w')
        json.dump(config, runconfig_file, sort_keys=True, indent=2)

        multi_machine_config = '\n'.join('config.vm.define "%d"' % i 
            for i in range(kwargs['multi_machine']))

        with open(path.join(self.path, 'Vagrantfile'), 'w') as vagrantfile:
            vagrantfile.write('''
Vagrant.configure(2) do |config|
  config.vm.box = "ac-cloud"%s
end
''' % ('\n' + multi_machine_config) if kwargs['multi_machine'] > 1 else '')

        self.config = Config(config)

    def status(self):
        raise NotImplementedError

    # def run(self, **kwargs):
    #     self.init(**kwargs)
    #     self.start()

    def start(self):
        return self.call('up', '--provider', self.config.provider.name)

    def attach(self):
        self.call('ssh')

    def pull(self):
        machines = map(os.path.basename, glob.glob('.vagrant/machines/*'))
        if len(machines) > 1:
            for machine in machines:
                self.call('ssh', machine, '-c', 'for folder in /vagrant/results/*; do mv $folder $folder-{0}; done'.format(machine))
        self.call('rsync-pull')

    def archive(self, compress=None):
        archive_path = path.join(self.path, 'results.tar.gz')
        result_path = path.join(self.path, 'results')

        if compress is None:
            compress = not self.is_archived()

        if compress is None:
            raise ValueError('Archiving integrity is faulty')

        if compress == self.is_archived():
            logging.warning(
                'Archive is already {}. Trying to {} anyway'.format(
                    'compressed' if compress else 'decompressed',
                    'compress' if compress else 'decompress'))

        if compress:
            with tarfile.open(archive_path, mode='w:gz') as archive:
                archive.add('results')
            shutil.rmtree(result_path)
        else:
            with tarfile.open(archive_path, mode='r:gz') as archive:
                archive.extractall(path=self.path)
            os.remove(archive_path)

    def check(self, verbose=False):
        error = self.config.check()
        if error:
            print 'Errors found in configuration'
            print '\n'.join(error)
            print self.config
        else:
            print 'No error found in configuration'
            if verbose:
                print self.config

    def call(self, *args):
        arguments = list(args)
        arguments.insert(0, 'vagrant')
        result = 'Error in function call {}'.format(' '.join(args))
        try:
            result = subprocess.check_call(arguments, cwd=self.path)
            return result
        except subprocess.CalledProcessError:
            return result