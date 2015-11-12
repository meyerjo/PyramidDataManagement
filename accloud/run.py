import os
import os.path as path
import shutil
import sys
import tarfile
import datetime
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

    def link(self):
        self.config.expand()
        files = []

        for experiment in self.config.experiments:
            with open(os.path.join(
                      self.config.aclib_root,
                      experiment.config_file)) as config_file:
                aclib_config = json.load(config_file)
                scenario = aclib_config['scenarios'][experiment.scenario]
                files.append(scenario['pcs'])
                files.append(experiment.config_file)

                instance = aclib_config['instances'][scenario['instances']]
                files.append(os.path.join(
                             'scenarios',
                             instance['problem_type'],
                             experiment.scenario))
                files.append(os.path.join(
                    'instances',
                    instance['problem_type'],
                    'data',
                    scenario['instances']))
                files.append(os.path.join(
                    'instances',
                    instance['problem_type'],
                    'sets',
                    scenario['instances']))

                algorithm = aclib_config['algorithms'][scenario['algorithm']]
                files.append(os.path.join(
                    'target_algorithms',
                    algorithm['problem_type'][0]
                        if len(algorithm['problem_type']) == 1 
                        else 'multi_problem',
                    scenario['algorithm']))

        def create_link(directory):
            folders, symlink = os.path.split(os.path.join(self.path, 'aclib', directory))
            os.makedirs(folders)
            os.symlink(
                os.path.join(self.config.aclib_root, directory),
                os.path.join(folders, symlink))

        # Delete links to subfolders of other links
        essential_links = []
        for f in sorted(files):
            if essential_links and f.startswith(essential_links[-1]):
                continue
            else:
                essential_links.append(f)

        for link in essential_links:
            create_link(link)

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
                'provider': kwargs['provider'],
                kwargs['provider']: {},
                'multi-machine': kwargs['multi_machine']
            },
            'include': ['~/.accloud/credentials.json'],
            'auto_teardown': kwargs['auto_teardown']
        }

        if kwargs['instance']:
            config['machine'][kwargs['provider']]['category'] = kwargs['instance']
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
  config.vm.box = "ac-cloud"
  config.vm.box_version = "0.2.0"%s
end
''' % ('\n' + multi_machine_config if kwargs['multi_machine'] > 1 else ''))

        self.config = Config(config)

    def monitor(self):
        # Check how long the experiment will last
        experiment_time = 30

        print('Experiment will finish at {:%x %X}'.format(
              datetime.datetime.now()
              + datetime.timedelta(seconds=experiment_time)))
        try:
            time.sleep(experiment_time)
            while(True):
                print('Checking experiment status')
                if self.finished():
                    print('Experiment finished')
                    self.pull()
                    self.teardown()
                else:
                    print('Experiment not finished, check again in 10 Minutes')
                    time.sleep(600)
        except KeyboardInterrupt:
            print('Monitoring aborted')
            return

    def finished(self):
        results = self.call_vm(
            'screen -ls | grep -E "There (is a|are) screens? on:"')

        for r in results:
            if r == 0:
                return False
        return True

    def run(self, **kwargs):
        self.create(**kwargs)
        self.start()

    def start(self):
        return self.call('up', '--provider', self.config.machine.provider)
        if self.config.auto_teardown:
            self.teardown()

    def attach(self):
        self.call('ssh')

    def teardown(self):
        self.pull()
        self.destroy()

    def pull(self):
        self.call_vm('for folder in /vagrant/results/*; '
                     'do mv $folder $folder-{machine}; done')
        self.call('rsync-pull')

    def destroy(self):
        self.call('destroy', '-f')

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

    def call_vm(self, arg):
        machines = map(os.path.basename, glob.glob('.vagrant/machines/*'))
        results = [self.call('ssh', machine, '-c',
                             arg.format(machine=machine,
                                        machine_number=machine_number))
                   for machine_number, machine in enumerate(machines)]
        return results
