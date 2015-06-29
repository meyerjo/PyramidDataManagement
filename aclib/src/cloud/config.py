'''Configuration of an cloud/VM based AClib run'''
import json

class Config(object):
    def __init__(self):
        self.config = dict(default_config)

    def load(self, fp):
        loaded_dict = json.load(fp)
        self.config.update(loaded_dict)

    def expand(self):
        single_experiment = self.config.pop('experiment', None)
        if single_experiment:
            self.config['experiments'].append(single_experiment)
            self.config['experiment'] = None

        assert self.config['experiments']

        expanded_experiments = []
        for exp in self.config['experiments']:
            default = DEFAULT_CONFIG['experiment'].copy()
            default['name'] = self.config['name']
            default.update(exp)
            expanded_experiments.append(default)

        multiplied_experiments = []
        for exp in expanded_experiments:
            if exp['repetition'] == 1:
                multiplied_experiments.append(exp)
            for i in range(exp['repetition']):
                instanced_exp = exp.copy()
                instanced_exp['repetition'] = 1
                instanced_exp['name'] += '-{0:02d}'.format(i)
                multiplied_experiments.append(instanced_exp)

        self.config['experiments'] = multiplied_experiments

    def __getattr__(self, name):
        try:
            return self.config[name]
        except KeyError:
            raise AttributeError


class Required(object):
    '''Class indicating that this object is required to be overwritten'''
    def __str__(self):
        raise NotImplementedError

DEFAULT_CONFIG = {
    "name": Required(),
    "debug": False,
    "parallel_runs": 1,
    "experiment": {
        "configurator": Required(),
        "scenario": Required(),
        "repetition": 1,
        "config_file": "src/data/config.json",  # Issue: How to resolve path?
        "seed": 1,
        "only_prepare": False
    },
    "experiments": [],
    "machine": {
        "cores": 1,
        "memory": 1024,
        "azure": {
            "category": "Small",
            "location": "West Europe"
        },
        "multi-machine": 1
    }
}
