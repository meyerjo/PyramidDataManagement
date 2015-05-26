#!/usr/bin/env python2.7


import json
import sys
import os
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=argparse.FileType('r', 0), default=sys.stdin)
    args = parser.parse_args()
    config = json.load(args.config)

    aclib_root = import_aclib(config['aclib_path'])
    import run_scenario as runner
    import install_scenario

    config.setdefault('config_file', os.path.join(aclib_root, "src", "data", "config.json"))
    config.setdefault('seed', 1)
    config.setdefault('working_directory', os.getcwd())

    installer = install_scenario.Installer(config['config_file'])
    installer.install_single_scenario(config['scenario'])

    configurators = {
        'ParamILS': runner.ParamILSRunner,
        'SMAC': runner.SMACRunner,
        'irace': runner.IRaceRunner
    }

    configurator = configurators[config['configurator']](
        config['config_file'],
        config['scenario'],
        aclib_root,
        config['working_directory'])

    configurator.prepare(config['seed'])

    try:
        configurator.run_scenario()
    except (KeyboardInterrupt, SystemExit):
        ### handle keyboard interrupt ###
        configurator.cleanup()
        return 1


# Workaround to import aclib modules. Maybe change this by integrating into
# aclib src or packaging aclib
def import_aclib(paths):
    def import_path(path):
        '''Predicate to check and import an aclib path'''
        if os.path.isdir(path):
            src_path = os.path.join(path, 'src')
            if os.path.isdir(src_path):
                sys.path.insert(0, src_path)
                return True

    return filter(import_path, paths)[0]


if __name__ == '__main__':
    main()
