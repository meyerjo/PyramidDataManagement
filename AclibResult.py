'''Classes representing the results of an AClib configuration run

'''

import csv
import os

class AclibResult(object):
    '''Reads and contains results of a Aclib Configuration run'''

    def merge_with(self, other):
        '''Merge this results of this run with a similar run
        Will work only when the runs are pretty similar and probably not
        across different configurators
        '''
        raise NotImplementedError


class SmacResult(AclibResult):
    '''Reads and contains results of a SMAC Configuration run'''
    def __init__(self):
        self.results = []

    def load_runs_and_results(self, filepath):
        '''Read in a runs_and_results csv file
        :param filepath: Path to CSV file
        '''
        with open(filepath) as csvfile:
            reader = csv.DictReader(csvfile)
            self.results = list(reader)

    def merge_with(self, other):
        '''Merge this results of this run with a similar run
        This makes sense if two runs with the same parameters and scenario
        should be joined together

        :param other: Similar SMACresult
        '''
        self.results += other.results


def merge_several_runs(path, scenario_data=None):
    '''Reads all runs in a result folder and merges them by same scenario

    :param path: The main result folder of the experiment. Basically the
    parent folder of the runs working directory
    :param scenario_data: A dictionary in which new results from path will be
    merged with, to be able to use many paths. By default a new dict is
    created.
    :returns: A dictionary containing the results keyed by scenario. Several
    runs of the same scenario will be merged.
    '''
    if not scenario_data:
        scenario_data = {}

    path_to_runs = os.path.join('smac-output', 'aclib', 'state-run1', 'runs_and_results-it0.csv')

    runs = (f for f in os.listdir(path)
            if os.path.isdir(os.path.join(path, f)))

    for folder in runs:
        run_result_path = os.path.join(path, folder, path_to_runs)
        if not os.path.isfile(run_result_path):
            continue

        scenario = folder[:-3]

        merged_results = scenario_data.setdefault(scenario, SmacResult())

        run_result = SmacResult()
        run_result.load_runs_and_results(run_result_path)
        merged_results.merge_with(run_result)

    return scenario_data
