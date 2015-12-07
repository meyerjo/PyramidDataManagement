#!/usr/bin/env python2
from __future__ import division, print_function
import argparse
from accloud import AclibResult, paths
import numpy as np
import test
import itertools
import tabulate
import logging
import sys
import os
import csv

args = argparse.Namespace()

def adapted_significance(comparisions, level=0.05):
    return (1 - (1 - level) ** (1 / comparisions))

def compare_validation_groups(folders):
    groups = []
    rest = folders
    try:
        while(True):
            delimiter = rest.index('vs.')
            groups.append(rest[:delimiter])
            rest = rest[delimiter+1:]
    except ValueError:
        groups.append(rest)

    if len(groups) == 1:
        logging.critical('Seperate groups by vs.')
        return 1

    data = (paths.sorted_scenario_data(group)[1] for group in groups)
    
    prev = None
    print('Adapted significance level {:0.4f}'.format(adapted_significance(len(groups) - 1)))
    for current in data:
        if not prev:
            prev = current
            continue

        p, diff = test.hybrid_permutation(np.hstack(prev), np.hstack(current))

        print('Significance level {:0.4f} with mean difference {}'.format(p, diff))


def compare_validation_results(folders):
    scenarios, data = paths.sorted_scenario_data(folders)
    compare_validation_factor(scenarios, data)


def compare_validation_factor(factors, values):
    n = len(values)
    results = [['' for _ in range(n)] for _ in range(n)]

    level = adapted_significance((n / 2) * (n - 1))

    for (i, y), (j, z) in itertools.combinations(enumerate(values), 2):
        p = test.exact_permutation(y, z)
        if p < level:
            print factors[i], factors[j]
        results[j][i] = p

    print tabulate.tabulate(results, headers=factors)
    print 'Adapted variance: %f' % adapted_significance
    

def compare_single_lingeling_runs(paths):
    run_datas = []
    common_scenarios = set()
    for path in paths:
        result = AclibResult.merge_several_runs(path)
        run_datas.append(result)
        if not common_scenarios:
            common_scenarios = set(result.keys())
        common_scenarios.intersection_update(result.keys())

    for scenario in common_scenarios:
        print(scenario)
        means = []
        stds = []
        for result in run_datas:
            response = np.array([float(r['Response Value (y)'])
                                 for r in result[scenario].results])
            means.append(np.mean(response))
            stds.append(np.std(response))
        difference = np.abs(means[0] - means[1]) / (stds[0] * stds[1])

        if difference > 30:
            print(difference)


def main():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('paths', type=str, nargs='+')
    parser.add_argument('--output', '-o')
    parser.add_argument('--mirror', action='store_true')

    comparer = {
        'lingeling': compare_single_lingeling_runs,
        'validation': compare_validation_results,
        'grouped': compare_validation_groups
    }

    parser.add_argument('--mode', '-m', choices=comparer.keys(), default='validation')
    args = parser.parse_args()

    comparer[args.mode](args.paths)
 


if __name__ == '__main__':
    main()
