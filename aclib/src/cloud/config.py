'''Configuration of an cloud/VM based AClib run'''
import json


class Config(object):
    '''Convience object containting the configuration'''
    def __init__(self, default=None):
        self.config = dict(default if default else DEFAULT_CONFIG)

        for key, value in self.config.items():
            if isinstance(value, dict):
                self.config[key] = Config(value)
            if isinstance(value, list):
                self.config[key] = list(Config(v) for v in value)

    def update(self, other):
        for key, value in other.config.iteritems():
            if key in self.config:
                if isinstance(value, Config):
                    self.config[key].update(value)
                elif isinstance(value, list):
                    self.config[key] += value
                else:
                    self.config[key] = value
            else:
                self.config[key] = value

    def __str__(self):
        valueprinter = {
            str: lambda s: '"{}"'.format(s),
            list: lambda l: '[\n{}\n]'.format(',\n'.join(map(str, l))),
            bool: lambda b: str(b).lower()
        }

        def printer(value):
            return valueprinter.get(type(value), str)(value)

        items = '\n' + ',\n'.join('"{}": {}'.format(k, printer(v))
                                  for k, v in self.config.iteritems())
        indented_items = '\n  '.join(items.split('\n'))
        return '{{{}\n}}'.format(indented_items)

    def check(self):
        '''Perform consistency checks on the configuration

        :return: List of errors
        '''

        for key, value in self.config.iteritems():
            if isinstance(value, Config):
                errors = value.check()
                if errors:
                    errors.insert(0, 'Error in field "{}"'.format(key))
                    return errors
            if isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, Config):
                        errors = item.check()
                        if errors:
                            errors.insert(0, 'Error in list "{}" at item {}'.
                                          format(key, i))
                            return errors
        return []


    def load(self, fp):
        loaded_dict = Config(json.load(fp))
        self.update(loaded_dict)

    def expand(self):
        single_experiment = self.config.pop('experiment', None)
        if single_experiment:
            self.config['experiments'].append(single_experiment)

        assert self.config['experiments']

        expanded_experiments = []
        for exp in self.experiments:
            default = Config(DEFAULT_CONFIG['experiment'])
            default.config['name'] = self.name
            default.update(exp)
            expanded_experiments.append(default)

        multiplied_experiments = []
        for exp in expanded_experiments:
            if exp.repetition == 1:
                multiplied_experiments.append(exp)
            else:
                print('Multiplying experiment {} {} times'.format(
                    exp.name, exp.repetition))
                for i in range(exp.repetition):
                    instanced_exp = Config(exp.config)
                    instanced_exp.config['repetition'] = 1
                    instanced_exp.config['name'] += '-{0:02d}'.format(i)
                    multiplied_experiments.append(instanced_exp)

        self.config['experiments'] = multiplied_experiments

    def __getattr__(self, name):
        try:
            return self.config[name]
        except KeyError:
            raise AttributeError


class Required(Config):
    '''Class indicating that this object is required to be overwritten'''
    
    def __init__(self):
        self.config = {}

    def check(self):
        return ["Required value is missing"]

    def __str__(self):
        return "<Required value>"

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
