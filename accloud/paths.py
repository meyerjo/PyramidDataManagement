import glob
import logging
from os.path import join

def validationResultPaths(path):

    resultpaths = [
    'results/*/validate-inc/validationResults-*.csv',
    'results/*/*/SMAC/run-1/validate-inc/*Results*.csv',
    'validate-test/validationResults-tunertimecsscWorkerValid_*.csv',
    '*/SMAC/run-*/validate-inc/validationResults-traj-run-*-walltimelocal.csv',
    '*/SMAC/run-*/validate-inc/validationResults-tunertimelocal-run*.csv',
    'default/SMAC/run-1/validate-def/validationResults-cli-1-walltimelocal.csv']

    validation_dirs = [f for val in resultpaths for f in glob.glob(join(path, val))]

    logging.debug('Found %d dirs in %s:\n%s' %
                  (len(validation_dirs), path, '\n'.join(validation_dirs)))

    if len(validation_dirs) == 0:
        logging.error('No validation results found in %s' % path)

    return validation_dirs