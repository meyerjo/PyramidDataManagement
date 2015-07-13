#!/usr/bin/env python2.7

import os
import argparse
import webbrowser
import server

parser = argparse.ArgumentParser()
parser.add_argument(
    'dir',
    nargs='?',
    default=os.getcwd(),
    help='Root directory for webserver [default "."]')
parser.add_argument(
    '--port', '-p',
    nargs='?',
    default=8000,
    type=int,
    help='Port the application runs under')
parser.add_argument(
    '--debug',
    action='store_true')
args = parser.parse_args()

if not args.debug:
    webbrowser.open_new_tab('http://localhost:{port}'.format(**vars(args)))

settings = {
    'root_dir': args.dir,
    'port': args.port,
    'trace': args.debug
}
if args.debug:
    import pdb
    try:
        server.serve(**settings)
    except KeyboardInterrupt:
        pass
    except:
        pdb.post_mortem()
else:
    server.serve(**settings)