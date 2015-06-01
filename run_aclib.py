#!/usr/bin/env python2.7
from __future__ import print_function
import json
import sys
import os
import argparse
from threading import Thread


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
    config = json.load(args.config)
    config['experiment'].setdefault('repetition', 1)
    config['experiment'].setdefault(
        'config_file', os.path.join(aclib_root, "src", "data", "config.json"))
    config['experiment'].setdefault('seed', 1)
    config['experiment'].setdefault('parallel', False)

    total_runs = config['experiment']['repetition']

    run_threads = []
    for i in range(total_runs):
        predecessor = run_threads[-1] if (run_threads and not config['experiment']['parallel']) else None
        run_threads.append(ExperimentRunner(i, config, predecessor))
        run_threads[-1].start()

    try:
        while True:
            time.sleep(3600)  # Non busy waiting ;)
    except (KeyboardInterrupt):
            print("Exiting due to KeyboardInterrupt", file=sys.stderr)
            sys.exit(1)


class ExperimentRunner(Thread):

    def __init__(self, counter, config, wait_for=None):
        Thread.__init__(self, name='ac-{0:s}-{1:02d}'.format(
            config['experiment']['name'],
            counter))

        self.previous_thread = wait_for

        installer = install_scenario.Installer(config['experiment']['config_file'])
        installer.install_single_scenario(config['experiment']['scenario'])

        self.configurator = self.configurators[config['experiment']['configurator']](
            config['experiment']['config_file'],
            config['experiment']['scenario'],
            aclib_root,
            config['experiment']['name'])

        self.configurator.prepare(config['experiment']['seed'])

    configurators = {
        'ParamILS': runner.ParamILSRunner,
        'SMAC': runner.SMACRunner,
        'irace': runner.IRaceRunner
    }

    def run(self):
        if self.previous_thread:
            self.previous_thread.join()

        try:
            self.configurator.run_scenario()
        except (KeyboardInterrupt, SystemExit):
            ### handle keyboard interrupt ###
            self.configurator.cleanup()
            return 1





if __name__ == '__main__':
    main()
