#!/usr/bin/env python2
from __future__ import division
import argparse
from accloud import AclibResult, paths
import numpy as np
import test
import itertools
import tabulate


def compare_validation_results(folders):
    scenarios, data = paths.sorted_scenario_data(folders)
    compare_validation_factor(scenarios, data)


def compare_validation_factor(factors, values):
    n = len(values)
    results = [[None for _ in range(n)] for _ in range(n)]

    comparisons = (n / 2) * (n - 1)
    adapted_significance = (1 - 0.95 ** (1 / comparisons))

    for (i, y), (j, z) in itertools.combinations(enumerate(values), 2):
        p = test.exact_permutation(y, z)
        if p < adapted_significance:
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('paths', type=str, nargs='+')

    comparer = {
        'lingeling': compare_single_lingeling_runs,
        'validation': compare_validation_results
    }

    parser.add_argument('--data_format', '-df', choices=comparer.keys(), default='validation')
    args = parser.parse_args()

    comparer[args.data_format](args.paths)
 


if __name__ == '__main__':
    main()
