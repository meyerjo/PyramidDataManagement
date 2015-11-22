'''HTTP Server and Request Handlers to explore ACcloud experiments'''
import jsonpickle
from pyramid.httpexceptions import HTTPFound
from pyramid.config import Configurator
from pyramid.static import static_view
from wsgiref.simple_server import make_server
import views
import os


def serve(**settings):
    config = Configurator(settings=settings)
    config.include('pyramid_chameleon')
    if settings['trace']:
        config.include('pyramid_debugtoolbar')

    config.registry.settings['directory_settings'] = dict()
    config.registry.settings['reload_templates'] = True
    for root, dirs, files in os.walk(config.registry.settings['root_dir']):
        if '.settings.json' in files:
            root = os.path.abspath(root)
            filename = root + '\\.settings.json'
            with open(os.path.join(filename), "r") as myfile:
                data = myfile.read()
                config.registry.settings['directory_settings'][root] = \
                    jsonpickle.decode(data)
            config.registry.settings['directory_settings'][root]['reload'] = config.registry.settings['reload_templates']
            config.registry.settings['directory_settings'][root]['path'] = filename

    dir_path = r'([\w\-\_]*\/)*'
    file_basename = r'[\w\-\_\.]*'

    config.add_route('markdown', '/{file:' + dir_path + file_basename + '\.md}')
    config.add_route('csv', '/{file:' + dir_path + file_basename + '\.csv}')
    config.add_route('csv_delimiter', '/{file:' + dir_path + file_basename + '\.csv}/{delimiter}')
    config.add_route('matlab', '/{file:' + dir_path + file_basename + '\.m}')
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
