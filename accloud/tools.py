import os
import argparse


class ReadableDir(argparse.Action):
    '''Argparse Action for a directory that exists and is readable
    Props to http://stackoverflow.com/a/11415816/1959450
    '''
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir = values
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError(
                "ReadableDir:{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace, self.dest, prospective_dir)
        else:
            raise argparse.ArgumentTypeError(
                "ReadableDir:{0} is not a readable dir".format(
                    prospective_dir))
