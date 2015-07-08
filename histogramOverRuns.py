#!/usr/bin/env python2.7
import numpy as np
import matplotlib.pyplot as plt
import argparse
import csv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('responses', type=argparse.FileType('r'))
    args = parser.parse_args()

    every_second_line = (line for i, line in enumerate(args.responses) if i % 2 == 1)
    results = csv.reader(every_second_line)
    runtimes = np.array([float(column[1]) for column in results])

    plt.hist(runtimes, 50)
    plt.show()

if __name__ == '__main__':
    main()
