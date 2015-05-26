#!/usr/bin/env python


import json
import sys
import argparse
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=argparse.FileType('r', 0), default=sys.stdin)
    args = parser.parse_args()
    config = json.load(args.config)

    subprocess.call(["python", "aclib/src/run_scenario.py", "-s", config["scenario"], "-c", config["configurator"]], stdout=sys.stdout, stderr=sys.stderr)


if __name__ == '__main__':

    # Workaround to import aclib modules. Maybe change this by integrating into
    # aclib src or packaging aclib

    def append_path(path):
        import os
        if os.path.isdir(path):
            sys.path.insert(0, path)

    append_path('../../aclib/src')
    append_path('/home/aclib/aclib/src')
    from downloader import Downloader
    main()
