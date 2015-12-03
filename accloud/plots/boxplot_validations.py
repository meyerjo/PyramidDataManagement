#!/usr/bin/env python2

'''Draw boxplot from average validation results'''

from accloud import AclibResult, paths
import argparse
import logging
import matplotlib.pyplot as plt
import numpy as np
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    parser.add_argument('--verbose', '-v', action='count', default=0)
    parser.add_argument('--output', '-o', help='Name for output files')
    parser.add_argument('--objective', choices=['runtime', 'quality'], default='runtime')
    args = parser.parse_args()

    logging.getLogger().setLevel(max(10, args.verbose * -10 + 40))

    names, scenario_data = paths.sorted_scenario_data(args.files, objective=args.objective)

    fig = plt.figure(figsize=(8, 5))
    fig.suptitle(os.path.dirname(args.files[0]).replace('_', '-'))
    boxplot = fig.add_subplot(111)
    boxplot.boxplot(scenario_data, showfliers=False)
    for i, data in enumerate(scenario_data):
        x = np.random.normal(i + 1, 0.01, size=len(data))
        boxplot.scatter(x, data, marker='.', color='r', alpha=0.4)
    boxplot.xaxis.set_ticklabels(map(os.path.basename, names), rotation=90)
    boxplot.xaxis.set_label_text('Machine')
    if args.objective == 'runtime':
        boxplot.set_yscale('log')
        boxplot.yaxis.set_label_text('Validation Mean Runtime [s]')
    else:
        boxplot.yaxis.set_label_text('Validation Mean Quality')
    plt.show()
    if args.output:
        fig.tight_layout()  
        fig.savefig('%s.pdf' % args.output, bb_inches='tight', transparent=True)
        fig.savefig('%s.png' % args.output, dpi=300, bb_inches='tight')

if __name__ == '__main__':
    main()
