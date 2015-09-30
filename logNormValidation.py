#!/usr/bin/env

'''Estimate lognormal distribution and show actual distribution of validated runs'''

from __future__ import division
import numpy as np
import argparse
from scipy.stats import lognorm, norm, cumfreq
from math import log

color = [(0.9375, 0.63671875, 0.99609375), (0.0, 0.45703125, 0.859375), (0.59765625, 0.24609375, 0.0), (0.296875, 0.0, 0.359375), (0.09765625, 0.09765625, 0.09765625), (0.0, 0.359375, 0.19140625), (0.16796875, 0.8046875, 0.28125), (0.99609375, 0.796875, 0.59765625), (0.5, 0.5, 0.5), (0.578125, 0.99609375, 0.70703125), (0.55859375, 0.484375, 0.0), (0.61328125, 0.796875, 0.0), (0.7578125, 0.0, 0.53125), (0.0, 0.19921875, 0.5), (0.99609375, 0.640625, 0.01953125), (0.99609375, 0.65625, 0.73046875), (0.2578125, 0.3984375, 0.0), (0.99609375, 0.0, 0.0625), (0.3671875, 0.94140625, 0.9453125), (0.0, 0.59765625, 0.55859375), (0.875, 0.99609375, 0.3984375), (0.453125, 0.0390625, 0.99609375), (0.59765625, 0.0, 0.0), (0.99609375, 0.99609375, 0.5), (0.99609375, 0.99609375, 0.0), (0.99609375, 0.3125, 0.01953125)]
def runtimeFromMergedValidations(files):
    return np.array([np.genfromtxt(f, delimiter=',', skip_header=True, usecols=(2)) for f in files])


def plotRuntimes(runtimes, fig):
    boxplot = fig.add_subplot(111)
    for runtime in runtimes:
        boxplot.boxplot(runtimes)
        boxplot.set_yscale('log')
        boxplot.yaxis.set_label_text('runtime [s]')
    return boxplot

def compareTwoSets(data1, data2, dist=lognorm):
    min1 = np.min(np.hstack((data1, data2)))

    params1 = fit(dist, data1)
    params2 = fit(dist, data2)

    pMin1 = 1 - dist.cdf(min1, *params1)
    pMin2 = 1 - dist.cdf(min1, *params2)

    return np.log(pMin1) / np.log(pMin2)




def ecdf(data, fig, color, name):


    def clone(data):
        x = data * 2
        x[::2] = data
        x[1::2] = data

        return x

    x = clone(sorted(data.tolist()))

    space = np.linspace(0, 1, len(data) + 1).tolist()
    y = np.array(clone(space)[1:-1])

    
    plt.plot(x, y, 'x-', color=color, label='ECDF %s' % name)

    return x, y





from os import listdir
from os.path import join
import glob
def validationResultPaths(path):
    resultpaths = [
    'results/*/validate-inc/*Results*.csv',
    'validate-test/validationResults-tunertimecsscWorkerValid_*.csv']
 
    return [f for val in resultpaths for f in glob.glob(join(path, val))]

distributions = dict(logN=lognorm, norm=norm)

parser = argparse.ArgumentParser()
parser.add_argument('files', nargs='+')
parser.add_argument('--plot', action='store_true')
parser.add_argument('--dist', choices=distributions, default='logN')
args = parser.parse_args()


data = [runtimeFromMergedValidations(validationResultPaths(d)) for d in args.files]


# print(np.min(data))
# print(lognorm.fit(data))

def fit(dist, data):
    return dist.fit(data, floc=0 if dist==lognorm else None)

if args.plot:
    import matplotlib.pyplot as plt
    fig2 = plt.figure()
    fig2.xlabel = 'Time (ms)'
    fig2.ylabel = 'CDF'



    dist = distributions[args.dist]

    for name, d, color in zip(args.files, data, color):
        ecdf(d, fig2, color, name)
        p = fig2.add_subplot(111)
        minimum = min(np.concatenate(data))
        maximum = max(np.concatenate(data))
        x = np.logspace(log(minimum, 10)-0.5, log(maximum, 10)+0.5, 200)
        p.set_xscale('log', basex = 10)
        params = fit(dist, d)
        p.plot(x, dist.cdf(x, *params), '-', color=color, label='logN %s' % name)
        
        factor = compareTwoSets(data[0], d, dist)
        print('%s/%s: %1.2fx' % (name, args.files[0], factor))
        print('Mean %1.2f Variance %1.4f Skew %1.2f' % dist.stats(*params, moments='mvs'))

    plt.title('')
    plt.xlabel('Time (s)')
    plt.ylabel('CDF')
    plt.legend(loc=4)
    plt.show()


