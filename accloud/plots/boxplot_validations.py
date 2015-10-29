#!/usr/bin/env python2

'''Draw boxplot from average validation results'''

from accloud.paths import validationResultPaths
import argparse
import logging
import matplotlib.pyplot as plt
import numpy as np


def runtimeFromMergedValidations(files):
    return np.array([np.genfromtxt(f, delimiter=',', skip_header=True, usecols=(2)) for f in files])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    parser.add_argument('--verbose', '-v', action='count', default=0)
    args = parser.parse_args()

    logging.getLogger().setLevel(max(10, args.verbose * -10 + 40))

    scenario_data = [runtimeFromMergedValidations(validationResultPaths(d)) for d in args.files]

    scenario_runtimes = []
    labels = []

    fig = plt.figure()
    boxplot = fig.add_subplot(111)
    boxplot.boxplot(scenario_data)
    boxplot.xaxis.set_ticklabels(args.files, rotation='vertical')
    boxplot.xaxis.set_label_text('scenario')
    boxplot.set_yscale('log')
    boxplot.yaxis.set_label_text('runtime [s]')

    plt.show()


if __name__ == '__main__':
    main()
