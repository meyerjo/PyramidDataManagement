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
    main()
