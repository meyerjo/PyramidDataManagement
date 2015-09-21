#!/usr/bin/env python2

'''Draw boxplot from average validation results'''

import AclibResult
import argparse
import matplotlib.pyplot as plt
import numpy as np
import glob
from os import listdir
from os.path import join

def runtimeFromMergedValidations(files):
    return np.array([np.genfromtxt(f, delimiter=',', skip_header=True, usecols=(2)) for f in files])

def validationResultPaths(path):
    resultpaths = [
    'results/*/validate-inc/*Results*.csv',
    'validate-test/validationResults-tunertimecsscWorkerValid_*.csv']
 
    return [f for val in resultpaths for f in glob.glob(join(path, val))]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    args = parser.parse_args()

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
