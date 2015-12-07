import glob
import logging
import os
import numpy as np

def find_files(resultpaths, path):
    validation_dirs = [f for val in resultpaths for f in glob.glob(os.path.join(path, val))]

    logging.debug('Found %d dirs in %s:\n%s' %
                  (len(validation_dirs), path, '\n'.join(validation_dirs)))

    if len(validation_dirs) == 0:
        logging.error('No validation results found in %s' % path)

    return validation_dirs


def benchmark_validation_files(path):
    file_paths = [
        'results/*/validationRunResultLineMatrix-cli-*-walltimelocal.csv',
        '*/Benchmark/run-*/validationRunResultLineMatrix-cli-*-walltimelocal.csv'
    ]

    return find_files(file_paths, path)


def validationResultPaths(path):

    resultpaths = [
        'results/*/validate-inc/validationResults-*.csv',
        # 'results/*/*/SMAC/run-1/validate-inc/*Results*.csv',
        'validate-test/validationResults-tunertimecsscWorkerValid_*.csv',
        '*/SMAC/run-*/validate-inc/validationResults-traj-run-*-walltimelocal.csv',
        '*/SMAC/run-*/validate-inc/validationResults-tunertimelocal-run*.csv',
        '*/SMAC/run-1/validate-def/validationResults-cli-1-walltimelocal.csv']

    return find_files(resultpaths, path)

def validationQualityResultPaths(path):
    resultpaths = [
    'results/*/validate-inc/validationRunResultLineMatrix-traj-run-*-walltimelocal.csv',
    '*/SMAC/run-*/validate-inc/validationRunResultLineMatrix-traj-run-*-walltimelocal.csv',
    '*/SMAC/run-1/validate-def/validationRunResultLineMatrix-cli-1-walltimelocal.csv'
    ]

    return find_files(resultpaths, path)

def runtimeFromMergedValidations(files):
    return np.array([np.genfromtxt(f, delimiter=',', skip_header=True, usecols=(2)) for f in files])

def qualityFromMergedValidations(files):
    return np.array([np.genfromtxt(f, delimiter=',', skip_header=True, usecols=(5)) for f in files])

def sorted_scenario_data(paths, objective='runtime'):
    if objective == 'runtime':
        sorted_data = sorted([(d, runtimeFromMergedValidations(validationResultPaths(d))) for d in paths], key=lambda d: np.mean(d[1]))
    else:
        sorted_data = sorted([(d, qualityFromMergedValidations(validationQualityResultPaths(d))) for d in paths], key=lambda d: np.mean(d[1]))
    names = [d[0] for d in sorted_data]
    data = [d[1] for d in sorted_data]
    return (names, data)
