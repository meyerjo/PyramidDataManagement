#!/usr/bin/env python2

'''Draw boxplot from average validation results'''

from accloud import AclibResult, paths
import argparse
import logging
import matplotlib.pyplot as plt
import numpy as np

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    parser.add_argument('--verbose', '-v', action='count', default=0)
    parser.add_argument('--output', '-o', help='Name for output files')
    args = parser.parse_args()

    logging.getLogger().setLevel(max(10, args.verbose * -10 + 40))

    names, scenario_data = paths.sorted_scenario_data(args.files)

    scenario_runtimes = []
    labels = []

    fig = plt.figure()
    boxplot = fig.add_subplot(111)
    boxplot.boxplot(scenario_data, showfliers=False)
    for i, data in enumerate(scenario_data):
        x = np.random.normal(i + 1, 0.01, size=len(data))
        boxplot.scatter(x, data, marker='.', color='r', alpha=0.4)
    boxplot.xaxis.set_ticklabels(names)
    boxplot.xaxis.set_label_text('scenario')
    boxplot.set_yscale('log')
    boxplot.yaxis.set_label_text('runtime [s]')
    plt.show()
    if args.output:
        fig.tight_layout()  
        fig.savefig('%s.pdf' % args.output, bb_inches='tight', transparent=True)
        fig.savefig('%s.png' % args.output, dpi=300, bb_inches='tight')

if __name__ == '__main__':
    main()
