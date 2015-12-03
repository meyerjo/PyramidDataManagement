from __future__ import division, print_function
from accloud import paths
import logging
import argparse
import csv
import os
import numpy as np
import itertools
import sys
import matplotlib.pyplot as plt

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
        existing_list = data.get((line[0], line[1]), [])
        existing_list.append([int(line[1]), resultline[0], float(resultline[1])])
        data[(line[0], line[1])] = existing_list
    return data

def benchmark_stats(files):

    rundata = {}
    for p in files:
        for f in paths.benchmark_validation_files(p): 
            try:
                with open(os.path.join(f)) as resultfile:
                    rundata = read_runresultlinematrix(resultfile, rundata)
            except IOError as e:
                logging.error(e)

    if not rundata:
        raise Exception("No data found")


    stds = []
    means = []   

    no_timeout = 0
    no_crashed = 0
    for instance, data in rundata.iteritems():
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

    n = len(rundata)

    return dict(means=means, stds=stds, no_timeout=no_timeout, no_crashed=no_crashed, n=n, per_run=len(data))

def analyse_dataset(files):
    omitted = np.empty(len(files))
    corr_coef = np.empty(len(files))
    coef_var = np.empty(len(files))
    n = np.zeros(len(files))

    for i, f in enumerate(files):
        stats = None
        try:
            stats = benchmark_stats([f])
        except Exception:
            print('Benchmark invalid')
            continue

        omitted[i] = (stats['no_crashed'] + stats['no_timeout'])/ stats['n']
        corr_coef[i] = np.corrcoef(stats['stds'], stats['means'])[0,1]
        coef_var[i] = np.mean(np.array(stats['stds']) / np.array(stats['means']))
        n[i] = len(stats['stds']) * stats['per_run']

        print('{}, {}, {:.0%}, {:0.2f}, {:0.4f}'.format(f, n[i], omitted[i], corr_coef[i], coef_var[i]))
    
    try:
        print('{}, {}, {:.0%}, {:0.2f}, {:0.4f}'.format(f, np.sum(n), np.average(omitted, weights=n), np.average(corr_coef, weights=n), np.average(coef_var, weights=n)))
    except ZeroDivisionError:
        return
        # print('%CRASHED  '.format()
        # print('%TIMEOUT  {:.0%}'.format( / stats['n']))
        # finished_runs = 
        # print('Correlation coeficient:  out of %d runs' % (, finished_runs))
        # print('Coeficient of variance: ' % ())


def compare_dataset(files):
    if len(files) < 2:
        logging.critical('At least two dataset need to be provided and last one has to be meta')
    vm, meta = files[:-1], files[-1:]
    vm_stats = benchmark_stats(vm)
    meta_stats = benchmark_stats(meta)

    assert(meta[0].endswith('meta'))

    print(vm_stats['n'])
    print(meta_stats['n'])

    fig = plt.figure()

    fig.suptitle(os.path.dirname(files[0]).replace('_', '-'))
    scatterplot = fig.add_subplot(111, aspect='equal', xscale='log', yscale='log')
    scatterplot.xaxis.set_label_text('Means of tried instances [s]')
    scatterplot.yaxis.set_label_text('Standard deviation of tried instances')
    scatterplot.scatter(vm_stats['means'], vm_stats['stds'], color='g', marker='.', alpha=0.5, label='Cloud')
    scatterplot.scatter(meta_stats['means'], meta_stats['stds'], color='r', marker='.', alpha=0.5, label='Local')
    scatterplot.legend(loc='upper left')
    plt.show()

    return fig



def main():

    modes = {
        'analyse': analyse_dataset,
        'compare': compare_dataset
    }

    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    parser.add_argument('--mode', '-m', choices=modes.keys(), default='analyse')
    parser.add_argument('--verbose', '-v', action='count', default=0)
    parser.add_argument('--output', '-o', help='Name for output files')
    args = parser.parse_args()

    logging.getLogger().setLevel(max(10, args.verbose * -10 + 40))
    logging.getLogger().addHandler(ShutdownHandler(level=50))

    fig = modes[args.mode](args.files)

    if args.output:
        fig.tight_layout()  
        fig.savefig('/home/gothm/thesis/thesis/fig/%s.pdf' % args.output, bb_inches='tight', transparent=True)
        fig.savefig('%s.png' % args.output, dpi=300, bb_inches='tight')

class ShutdownHandler(logging.Handler):
    def emit(self, record):
        print(record.msg, file=sys.stderr)
        logging.shutdown()
        sys.exit(1)


logging.getLogger().addHandler(ShutdownHandler(level=50))

if __name__ == '__main__':
    main()