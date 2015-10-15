#!/usr/bin/env python2.7
import numpy as np
import matplotlib.pyplot as plt
import argparse
import csv
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('responses', type=argparse.FileType('r'))
    parser.add_argument('--save', '-s', action='store_true')
    args = parser.parse_args()

    every_second_line = (line for line in args.responses
                         if line.startswith('Result for ParamILS'))
    results = csv.reader(every_second_line)
    runtimes = np.array([float(column[1]) for column in results])

    fig = plt.figure()
    histogram = fig.add_subplot(111)

    histogram.hist(
        runtimes,
        bins=50)
    histogram.xaxis.set_label_text('runtime [s]')
    histogram.yaxis.set_label_text('#runs')

    plt.title(os.path.basename(args.responses.name))
    if args.save:
        path = args.responses.name + '.png'
        plt.savefig(path)
        print('Saved to "{}"'.format(path))
    else:
        plt.show()

if __name__ == '__main__':
    main()
