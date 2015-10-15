#!/usr/bin/env python2
import argparse
import AclibResult
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('paths', type=str, nargs='+')
    args = parser.parse_args()

    run_datas = []
    common_scenarios = set()
    for path in args.paths:
        result = AclibResult.merge_several_runs(path)
        run_datas.append(result)
        if not common_scenarios:
            common_scenarios = set(result.keys())
        common_scenarios.intersection_update(result.keys())

    for scenario in common_scenarios:
        print scenario
        means = []
        stds = []
        for result in run_datas:
            response = np.array([float(r['Response Value (y)'])
                                 for r in result[scenario].results])
            means.append(np.mean(response))
            stds.append(np.std(response))
        difference = np.abs(means[0] - means[1]) / (stds[0] * stds[1])

        if difference > 30:
            print difference


if __name__ == '__main__':
    main()
