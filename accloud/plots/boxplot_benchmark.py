from __future__ import division
import logging
import argparse
import csv
import os
import numpy as np
import itertools

def read_runresultlinematrix(f, data):
    ''' Reads a runsandresults file f and returns a dictionary with lists
    of runtimes listed by instance
    '''
    reader = csv.reader(f)
    header = True
    for line in reader:
        if header:
            header = False
            continue
        resultline = line[2].split(',')
        existing_list = data.get(line[0], [])
        existing_list.append([int(line[1]), resultline[0], float(resultline[1])])
        data[line[0]] = existing_list
    return data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    parser.add_argument('--verbose', '-v', action='count', default=0)
    args = parser.parse_args()

    logging.getLogger().setLevel(max(10, args.verbose * -10 + 40))

    data = {}

    for f in args.files:
        with open(os.path.join(f, 'validationRunResultLineMatrix-cli-1-walltimelocal.csv')) as resultfile:
            data = read_runresultlinematrix(resultfile, data)

    n = len(data)
    no_crashed = [d[1] for d in data.values()].count('CRASHED')
    print '%%CRASHED  %f' % (no_crashed / n)

    cumulated = sum((d[2] for d in itertools.chain(*data.values()) if d[1] != 'CRASHED'))
    print 'MEAN %f' % (cumulated / n)

    stds = []
    means = []   

    for instance, data in data.iteritems():
        runtimes = [d[2] for d in data]
        if 'TIMEOUT' in (d[1] for d in data):
            continue
        stds.append(np.std(runtimes))
        means.append(np.mean(runtimes))
        # print '%s: %.2f, %.2f, %.2f' % (instance, stds[-1], means[-1], stds[-1] / means[-1])

    print 'Correlation coeficient: %0.2f' % (np.corrcoef(stds, means)[0,1])


if __name__ == '__main__':
    main()