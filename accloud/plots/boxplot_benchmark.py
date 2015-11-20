from __future__ import division
from accloud import paths
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

    for p in args.files:
        for f in paths.benchmark_validation_files(p): 
            try:
                with open(os.path.join(f)) as resultfile:
                    data = read_runresultlinematrix(resultfile, data)
            except IOError as e:
                logging.error(e)

    if not data:
        raise Exception("No data found")


    stds = []
    means = []   

    no_timeout = 0
    no_crashed = 0
    for instance, data in data.iteritems():
        runtimes = [d[2] for d in data]
        if 'TIMEOUT' in (d[1] for d in data):
            no_timeout += 1
            continue
        if 'CRASHED' in (d[1] for d in data):
            no_crashed += 1
            continue
        stds.append(np.std(runtimes))
        means.append(np.mean(runtimes))
        # print '%s: %.2f, %.2f, %.2f' % (instance, stds[-1], means[-1], stds[-1] / means[-1])

    n = len(data)

    print '%CRASHED  {:.0%}'.format(no_crashed / n)
    print '%TIMEOUT  {:.0%}'.format(no_timeout / n)
    finished_runs = (n-no_timeout-no_crashed) * len(data)
    print 'Correlation coeficient: %0.4f out of %d runs' % (np.corrcoef(stds, means)[0,1], finished_runs)


if __name__ == '__main__':
    main()