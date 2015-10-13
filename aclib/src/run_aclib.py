#!/usr/bin/env python2.7
# Entry point script for cloud version AClib
from __future__ import print_function
import sys
import os
import argparse
from time import sleep
import multiprocessing
from cloud.config import Config
import install_scenario  # pylint: disable=f0401
import run_scenario as runner  # pylint: disable=f0401


def import_aclib():
    '''Workaround to import aclib modules. Maybe change this by integrating into
    aclib src or packaging aclib'''
    aclib_roots = [
        "../../aclib",
        "../../../aclib",
        "/home/aclib/aclib",
        "/vagrant/aclib"
    ]

    def import_path(path):
        '''Predicate to check and import an aclib path'''
        if os.path.isdir(path):
            src_path = os.path.join(path, 'src')
            if os.path.isdir(src_path):
                return True

    return next(p for p in aclib_roots if import_path(p))
__aclib_root__ = import_aclib()


def main():
    '''Start several AClib experiments with a provided runconfig file'''
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'config',
        type=argparse.FileType('r', 0),
        default=sys.stdin)
    args = parser.parse_args()

    config = Config()
    config.load(args.config)
    config.expand()
    errors = config.check()
    if errors:
        errors.insert(0, 'Error in configuration')
        print('\n'.join(errors))
        print('Complete configuration:')
        print(config)

    run_processes = []
    parallel_run_block = multiprocessing.Semaphore(config.parallel_runs)
    install_mutex = multiprocessing.Lock()

    for exp in config.experiments:
        run_processes.append(
            ExperimentRunner(exp, parallel_run_block, install_mutex))

    for process in run_processes:
        parallel_run_block.acquire()
        process.start()

    try:
        while True:
            sleep(3600)  # Non busy waiting ;)
    except KeyboardInterrupt:
        print("Exiting due to KeyboardInterrupt", file=sys.stderr)
        sys.exit(1)


class ExperimentRunner(multiprocessing.Process):
    '''Run an experiment in AClib in encapsulated in an own process'''
    def __init__(self, experiment, end_event, install_mutex):

        multiprocessing.Process.__init__(self, name=experiment.name)

        self.install_mutex = install_mutex
        self.release_on_exit = end_event
        self.config = experiment

    configurators = {
        'ParamILS': runner.ParamILSRunner,
        'SMAC': runner.SMACRunner,
        'irace': runner.IRaceRunner
    }

    def run(self):
        # Install scenario
        with self.install_mutex:
            print('Initializing experiment {}'.format(self.name))
            config_file = os.path.join(
                __aclib_root__,
                self.config.config_file)
            installer = install_scenario.Installer(config_file)
            installer.install_single_scenario(self.config.scenario)

            configurator = self.configurators[self.config.configurator](
                config_file,
                self.config.scenario,
                __aclib_root__,
                os.path.join('results', self.name))

            if self.config.validate and self.config.validate.mode == "TIME":
                configurator.prepare(
                    self.config.seed,
                    max_timestamp=self.config.validate.max,
                    min_timestamp=self.config.validate.min,
                    mult_factor=self.config.validate.factor)
            else:
                configurator.prepare(self.config.seed)

        # Run scenario
        try:
            if not self.config.only_prepare:
                print('Starting experiment {}'.format(self.name))
                configurator.run_scenario()
                if self.config.validate:
                    print('Starting validation {}'.format(self.name))
                    self.config.run_validate(
                        mode=self.config.validate.mode,
                        val_set=self.config.validate.set)
        except (KeyboardInterrupt, SystemExit):
            configurator.cleanup()
        finally:
            print('Experiment {} finished'.format(self.name))
            self.release_on_exit.release()


if __name__ == '__main__':
    main()
