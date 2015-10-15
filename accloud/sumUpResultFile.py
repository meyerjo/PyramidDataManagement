#!/usr/bin/env

'''Sum up validation results for single instances to average'''

from __future__ import division
from math import log
import argparse
import re
from scipy.stats import lognorm, norm, cumfreq
import numpy as np

def runtimeFromMergedValidations(f):
    return np.genfromtxt(f, delimiter=',', skip_header=True, usecols=(2))


def sumUpPath(path):
    data = runtimeFromMergedValidations(path)
    summed_up = np.array([[-1,-1,np.average(data)]])
    print summed_up
    header = '"Time","Training (Empirical) Performance","Test Set Performance","AC Overhead Time","Validation Configuration ID"'
    try:
        n = int(re.search(r'_smac-(\d+)_', string).group(1))
    except (ValueError, IndexError):
	print 'Cannot read number from filename'
        n = 1337
    np.savetxt(
        'validationResults-traj-run-{}-walltimelocal.csv'.format(n),
        summed_up,
        delimiter=',',
        header=header,
        fmt='%.9f')

parser = argparse.ArgumentParser()
parser.add_argument('files', nargs='+')
args = parser.parse_args()


for f in args.files:
    sumUpPath(f)

