#!/usr/bin/env python

'''Generate an overview json by traversing through experiments'''

import os
import json

def traverse_path(path):
    items = os.listdir(path)
    if "runconfig.json" in items:
        with open(os.path.join(path, 'runconfig.json')) as runconfig:
            data = json.load(runconfig)
            data['path'] = path
            yield data
    else:
        for item in items:
            folder = os.path.join(path, item)
            if os.path.isdir(folder) and item != 'meta':
                for item in traverse_path(folder):
                    yield item


def main():
    # Read in path or cwd
    directory = os.getcwd()

    # Traverse directory tree and build dictionary
    toc = list(traverse_path(directory))

    # Write out dict as json
    print json.dumps(toc, indent=2, sort_keys=True)

if __name__ == '__main__':
    main()
