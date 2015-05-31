#!/usr/bin/env python2.7
import json
import sys
import os
import argparse
import copy

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
    config['experiment'].setdefault('times', 1)

    total_runs = config['experiment']['times']
    for run_number in range(total_runs):
        exp_config = copy.deepcopy(config)
        if total_runs > 1:
            exp_config['experiment']['name'] += '_%d' % (run_number + 1)
        runner = ExperimentRunner()
        runner.set_configurator(exp_config)
        runner.run_configurator()


class ExperimentRunner(object):

    configurators = {
        'ParamILS': runner.ParamILSRunner,
        'SMAC': runner.SMACRunner,
        'irace': runner.IRaceRunner
    }

    def __init__(self):
        self.configurator = None

    def set_configurator(self, config):

        config['experiment'].setdefault(
            'config_file', os.path.join(aclib_root, "src", "data", "config.json"))
        config['experiment'].setdefault(
            'seed', 1)

        installer = install_scenario.Installer(config['experiment']['config_file'])
        installer.install_single_scenario(config['experiment']['scenario'])

        self.configurator = self.configurators[config['experiment']['configurator']](
            config['experiment']['config_file'],
            config['experiment']['scenario'],
            aclib_root,
            config['experiment']['name'])

        self.configurator.prepare(config['experiment']['seed'])

    def run_configurator(self):
        try:
            self.configurator.run_scenario()
        except (KeyboardInterrupt, SystemExit):
            ### handle keyboard interrupt ###
            self.configurator.cleanup()
            return 1





if __name__ == '__main__':
    main()
