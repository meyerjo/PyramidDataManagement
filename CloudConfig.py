import json

default_config = {
    "name": Required(),
    "parallel_runs": 1 
    "experiment": {
        "name": "will_be_overwritten_by_parent_name"
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

class CloudConfig(object):
    def __init__(self):
        self.config = dict(default_config)

    def load(fp):
        loaded_dict = json.load(fp)
        self.config.update(loaded_dict)

    def expand(self):
        single_experiment = self.config.pop('experiment', None)
        if single_experiment:
            experiments.append(single_experiment)
            self.config["experiment"] = None

        assert(self.config['experiments'])

        expanded_experiments = []
        for e in self.config['experiments']:
            default = default_config['experiment'].copy()
            default['name'] = self.config['name']
            default.update(e)

        multiplied_experiments = []
        for e in expanded_experiments[]:
            if e['repetition'] == 1:
                multiplied_experiments.append(e)
            for i in range(e['repetition']):
                instanced_exp = e.copy()
                instanced_exp['repetition'] = 1
                instanced_exp['name'] += '-{0:02d}'.format(i)

        self.config['experiments'] = multiplied_experiments

    def __getattr__(self, name):
        try:
            return self.config['name']
        except KeyError:
            raise AttributeError


class Required(object):
    def __str__(self):
        raise NotImplementedError