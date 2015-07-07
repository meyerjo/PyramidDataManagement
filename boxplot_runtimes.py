#!/usr/bin/env python2
import argparse
import AclibResult
from tools import ReadableDir
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', action=ReadableDir)
    args = parser.parse_args()

    scenario_data = AclibResult.merge_several_runs(args.path)

    scenario_runtimes = []
    labels = []
    for scenario, data in scenario_data.iteritems():
        response = np.array([float(r['Response Value (y)'])
                             for r in data.results])
        if np.mean(response) == 300:
            continue
        scenario_runtimes.append(response)
        labels.append(scenario)

    fig = plt.figure()
    boxplot = fig.add_subplot(111)
    boxplot.boxplot(scenario_runtimes)
    boxplot.xaxis.set_ticklabels(labels, rotation='vertical')
    boxplot.set_yscale('log')

    plt.show()


if __name__ == '__main__':
    main()
