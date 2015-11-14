#!/usr/bin/env python2

'''Create boxplots of single runtimes of a target algorithm'''

from __future__ import division
from accloud.tools import ReadableDir
from accloud import AclibResult
import argparse
import matplotlib.pyplot as plt
import numpy as np
import tabulate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', action=ReadableDir)
    parser.add_argument('--timeouts', action='store_true')
    parser.add_argument('--tablefmt', choices=tabulate.tabulate_formats, default='pipe')
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

    def ratio_outliers(data, m = 2.):
        d = np.abs(data - np.median(data))
        mdev = np.median(d)
        s = d/mdev if mdev else 0.
        return len(data[s>m]) / len(data)

    header = ['Scenario', 'Median', 'Mean', 'Std', 'Ratio Outliers']
    table = [[name, '%.2f' % np.median(data), '%.2f' % np.mean(data), '%.2f' % np.std(data), '%.2f' % ratio_outliers(data)] for data, name in runtime_data]
    print np.corrcoef([np.std(d) for d,_ in runtime_data],[np.mean(d) for d,_ in runtime_data])
    print np.average(np.array([np.std(d) for d,_ in runtime_data])/np.array([np.mean(d) for d,_ in runtime_data]))
    print(tabulate.tabulate(table, header, tablefmt=args.tablefmt))

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
