#!/usr/bin/env python2
import argparse
import os
import os.path as path
import shutil
import sys
import tarfile
import subprocess
import logging
import glob
from config import Config


class Run(object):
    '''Representation of an ACcloud vagrant box'''
    def __init__(self, boxpath):
        self.config = Config()
        self.path = boxpath

        if not path.isdir(boxpath):
            os.makedirs(boxpath)

        try:
            json = open(path.join(boxpath, 'runconfig.json'), 'r')
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

    def create(self):
        if self.config.loaded_files:
            logging.critical('Experiment already initialized')
            return

        self.call('init', 'master', '-m')
        result = self.start()

        if not result.split(',')[3] == 'Vagrant::Errors::ConfigInvalid':
            logging.error(
                'Error in the creation of vagrant box: {}').format(result[4])

    def status(self):
        raise NotImplementedError

    def start(self):
        return self.call('up', '--provider', 'azure')

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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--box',
                        type=str,
                        default=os.getcwd(),
                        help='Path to the experiment folder (a vagrant box)')

    parser.add_argument('--version', action='version', version='test')

    command = parser.add_subparsers()

    archive = command.add_parser('archive')
    archive.set_defaults(func=Run.archive)
    archive.set_defaults(sub=archive)
    archive.add_argument('--compress', '-c',
                         type=bool,
                         dest='compress',
                         help='Force compressing the experiment box')
    archive.add_argument('--decompress', '-d',
                         action='store_const',
                         const=False,
                         dest='compress',
                         help='Force extract the experiment box')

    check = command.add_parser('check')
    check.set_defaults(func=Run.check)
    check.set_defaults(sub=check)
    check.add_argument('--verbose', '-v',
                       action='store_true')

    init = command.add_parser('init')
    init.set_defaults(func=Run.create)
    init.set_defaults(sub=init)

    pull = command.add_parser('pull')
    pull.set_defaults(func=Run.pull)
    pull.set_defaults(sub=pull)

    attach = command.add_parser('attach')
    attach.set_defaults(func=Run.attach)
    attach.set_defaults(sub=attach)

    args = parser.parse_args()

    subargs = vars(args.sub.parse_known_args()[0])
    subargs.pop('func')
    subargs.pop('sub')

    args.func(Run(args.box), **subargs)


if __name__ == '__main__':
    if '--debug' in sys.argv:
        try:
            main()
        except:
            import pdb
            pdb.post_mortem()
    else:
        main()
