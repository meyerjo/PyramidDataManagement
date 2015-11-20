import glob
import logging
from os.path import join
import numpy as np

def find_files(resultpaths, path):
    validation_dirs = [f for val in resultpaths for f in glob.glob(join(path, val))]

    logging.debug('Found %d dirs in %s:\n%s' %
                  (len(validation_dirs), path, '\n'.join(validation_dirs)))

    if len(validation_dirs) == 0:
        logging.error('No validation results found in %s' % path)

    return validation_dirs


def benchmark_validation_files(path):
    file_paths = [
        'results/*/validationRunResults',
        '*/Benchmark/run-1/validationRunResultLineMatrix-cli-*-walltimelocal.csv'
    ]

    return find_files(file_paths, path)

def validationResultPaths(path):

    resultpaths = [
        'results/*/validate-inc/validationResults-*.csv',
        # 'results/*/*/SMAC/run-1/validate-inc/*Results*.csv',
        'validate-test/validationResults-tunertimecsscWorkerValid_*.csv',
        '*/SMAC/run-*/validate-inc/validationResults-traj-run-*-walltimelocal.csv',
        '*/SMAC/run-*/validate-inc/validationResults-tunertimelocal-run*.csv',
        'default/SMAC/run-1/validate-def/validationResults-cli-1-walltimelocal.csv']

    return find_files(resultpaths, path)

def runtimeFromMergedValidations(files):
    return np.array([np.genfromtxt(f, delimiter=',', skip_header=True, usecols=(2)) for f in files])

def sorted_scenario_data(paths):
    sorted_data = sorted([(d, runtimeFromMergedValidations(validationResultPaths(d))) for d in paths], key=lambda d: np.median(d[1]))
    names = [d[0] for d in sorted_data]
    data = [d[1] for d in sorted_data]
    return (names, data)
