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

    aclib_root = import_aclib(config['experiment']['aclib_path'])
    import run_scenario as runner
    import install_scenario

    config['experiment'].setdefault(
        'config_file', os.path.join(aclib_root, "src", "data", "config.json"))
    config['experiment'].setdefault(
        'seed', 1)

    installer = install_scenario.Installer(config['experiment']['config_file'])
    installer.install_single_scenario(config['experiment']['scenario'])

    configurators = {
        'ParamILS': runner.ParamILSRunner,
        'SMAC': runner.SMACRunner,
        'irace': runner.IRaceRunner
    }

    configurator = configurators[config['experiment']['configurator']](
        config['experiment']['config_file'],
        config['experiment']['scenario'],
        aclib_root,
        config['experiment']['name'])

    configurator.prepare(config['experiment']['seed'])

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
