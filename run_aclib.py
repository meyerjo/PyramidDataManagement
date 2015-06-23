#!/usr/bin/env python2.7
from __future__ import print_function
import json
import sys
import os
import argparse
from time import sleep
import multiprocessing
from CloudConfig import CloudConfig


# Workaround to import aclib modules. Maybe change this by integrating into
# aclib src or packaging aclib
aclib_roots = [
    "../../aclib",
    "../../../aclib",
    "/home/aclib/aclib",
    "/vagrant/aclib"
]


def import_aclib(paths):
    def import_path(path):
        '''Predicate to check and import an aclib path'''
        if os.path.isdir(path):
            src_path = os.path.join(path, 'src')
            if os.path.isdir(src_path):
                sys.path.insert(0, src_path)
                return True

    return filter(import_path, paths)[0]
aclib_root = import_aclib(aclib_roots)
import install_scenario
import run_scenario as runner


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=argparse.FileType('r', 0), default=sys.stdin)
    args = parser.parse_args()

    config = CloudConfig()
    config.load(args.config)
    config.expand()

    run_processes = []
    parallel_run_block = multiprocessing.Semaphore(
        config.parallel_runs)
    install_mutex = multiprocessing.Lock()

    for exp in config.experiments:
        run_processes.append(ExperimentRunner(exp, config, parallel_run_block, install_mutex))

    for process in run_processes:
        process.start()

    try:
        while True:
            sleep(3600)  # Non busy waiting ;)
    except (KeyboardInterrupt):
            print("Exiting due to KeyboardInterrupt", file=sys.stderr)
            sys.exit(1)


class ExperimentRunner(multiprocessing.Process):

    def __init__(self, experiment, end_event, install_mutex):

        multiprocessing.Process.__init__(self, name=experiment.['name'])

        print('Initializing experiment {}'.format(self.name))

        self.install_mutex = install_mutex
        self.release_on_exit = end_event
        self.config = experiment

    configurators = {
        'ParamILS': runner.ParamILSRunner,
        'SMAC': runner.SMACRunner,
        'irace': runner.IRaceRunner
    }

    def run(self):
        self.release_on_exit.acquire()
        print('Starting experiment {}'.format(self.name))

        with self.install_mutex:
            installer = install_scenario.Installer(self.config['config_file'])
            installer.install_single_scenario(self.config['scenario'])

            self.configurator = self.configurators[self.config['configurator']](
                os.path.join(aclib_root, self.config['config_file']),
                self.config['scenario'],
                aclib_root,
                os.path.join('results', self.name))

            self.configurator.prepare(self.config['seed'])

        try:
            if not self.config['only_prepare']:
                self.configurator.run_scenario()
        except (KeyboardInterrupt, SystemExit):
            ### handle keyboard interrupt ###
            self.configurator.cleanup()
            self.release_on_exit.release()
            return 1
        finally:
            self.release_on_exit.release()
        self.release_on_exit.release()

        print('Experiment {} finished'.format(self.name))


if __name__ == '__main__':
    main()
