from __future__ import division
import logging
import argparse
import csv
import os

def read_runresultlinematrix(f):
    data = {}
    reader = csv.reader(f)
    header = True
    for line in reader:
        if header:
            header = False
            continue
        resultline = line[2].split(',')
        data[line[0]] = [int(line[1]), resultline[0], float(resultline[1])]
    return data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    parser.add_argument('--verbose', '-v', action='count', default=0)
    args = parser.parse_args()

    logging.getLogger().setLevel(max(10, args.verbose * -10 + 40))

    for f in args.files:
        with open(os.path.join(f, 'validationRunResultLineMatrix-cli-1-walltimelocal.csv')) as resultfile:
            data = read_runresultlinematrix(resultfile)
            print f

            n = len(data)
            no_crashed = [d[1] for d in data.values()].count('CRASHED')
            print '%%CRASHED  %f' % (no_crashed / n)

            cumulated = sum((d[2] for d in data.values() if d[1] != 'CRASHED'))
            print 'MEAN %f' % (cumulated / n)
if __name__ == '__main__':
    main()