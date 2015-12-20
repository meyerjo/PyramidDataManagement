'''HTTP Server and Request Handlers to explore ACcloud experiments'''
import os
from wsgiref.simple_server import make_server

import jsonpickle
from pyramid.config import Configurator
from pyramid.static import static_view


def load_directory_settings(config):
    for root, dirs, files in os.walk(config.registry.settings['root_dir']):
        root = os.path.abspath(root)
        if '.settings.json' in files:
            lastfolder = os.path.abspath(root + '/..')
            last_settings = dict()
            if lastfolder in config.registry.settings['directory_settings']:
                last_settings = config.registry.settings['directory_settings'][lastfolder]

            config.registry.settings['directory_settings'][root] = last_settings

            filename = root + '/.settings.json'
            with open(os.path.join(filename), "r") as myfile:
                data = myfile.read()
                settings_struct = jsonpickle.decode(data)
                if not isinstance(settings_struct, dict):
                    settings_struct = jsonpickle.decode(settings_struct)

            try:
                settings_struct.update(config.registry.settings['directory_settings'][root])
                config.registry.settings['directory_settings'][root] = settings_struct
                config.registry.settings['directory_settings'][root]['reload'] = config.registry.settings[
                    'reload_templates']
                config.registry.settings['directory_settings'][root]['path'] = filename
            except Exception as e:
                print(e.message)

        else:
            path = os.path.abspath(root + '/..')
            if path in config.registry.settings['directory_settings']:
                config.registry.settings['directory_settings'][root] = \
                    config.registry.settings['directory_settings'][path]


def serve(**settings):
    config = Configurator(settings=settings)
    config.include('pyramid_chameleon')
    if settings['trace']:
        config.include('pyramid_debugtoolbar')

    config.registry.settings['directory_settings'] = dict()
    config.registry.settings['reload_templates'] = True

    # load directory settings
    load_directory_settings(config)

    dir_path = r'([\w\-\_]*\/)*'
    file_basename = r'[\w\-\_\.]*'

    fileroutes = [dict(route_name='markdown', file_extension='\.md', options=None),
                  dict(route_name='csv', file_extension='\.csv', options=None),
                  dict(route_name='csv_delimiter', file_extension='\.csv', options='/{delimiter}'),
                  dict(route_name='matlab', file_extension='\.m', options=None),
                  dict(route_name='matlabfileviewer', file_extension='\.mat', options=None),
                  dict(route_name='matlabfileviewer_subpath', file_extension='\.mat', options='/{subkeypath}'),
                  dict(route_name='jsonviewer', file_extension='\.json', options=None),
                  dict(route_name='jsonviewer_plain', file_extension='\.json', options='/json')]
    for fileroute in fileroutes:
        options = '' if fileroute['options'] is None else fileroute['options']
        options = options if options.startswith('/') or options == '' else '/' + options
        filepath = '/{file:' + dir_path + file_basename + fileroute['file_extension'] + '}'
        config.add_route(fileroute['route_name'], filepath + options)

    config.add_route('directory', '/{dir:' + dir_path + '}')
    config.add_route('static', '/_static/*subpath')
    config.add_route('files', '/*subpath')

    here = lambda p: os.path.join(os.path.abspath(os.path.dirname(__file__)), p)
    static = static_view(here('static'), use_subpath=True)
    files = static_view(
        os.path.abspath(config.registry.settings['root_dir']),
        use_subpath=True)

    config.add_view(static, route_name='static')
    config.add_view(files, route_name='files')
    config.scan()
    app = config.make_wsgi_app()
    print('Creating server')
    server = make_server('127.0.0.1', settings['port'], app)
    print('Start serving on port {}'.format(settings['port']))
    server.serve_forever()
