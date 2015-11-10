#!/usr/bin/env python2

'''Create boxplots of single runtimes of a target algorithm'''

from accloud.tools import ReadableDir
from accloud import AclibResult
import argparse
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', action=ReadableDir)
    parser.add_argument('--timeouts', action='store_true')
    args = parser.parse_args()

    scenario_data = AclibResult.merge_several_runs(args.path)

    runtime_data = []  # (runtime, label)
    for scenario, data in scenario_data.iteritems():
        response = np.array([float(r['Response Value (y)'])
                             for r in data.results])
        if not args.timeouts and np.median(response) == 300:
            continue
        runtime_data.append((response, scenario))

    runtime_data = sorted(runtime_data, key=lambda d: np.median(d[0]))
    fig = plt.figure()
    boxplot = fig.add_subplot(111)
    boxplot.boxplot([time for (time, label) in runtime_data], vert=False)
    boxplot.yaxis.set_ticklabels(
        [label for (time, label) in runtime_data])
    boxplot.yaxis.set_label_text('scenario')
    boxplot.set_xscale('log')
    boxplot.xaxis.set_label_text('runtime [s]')

    plt.show()


if __name__ == '__main__':
    main()
