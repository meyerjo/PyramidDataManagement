'''HTTP Server and Request Handlers to explore ACcloud experiments'''
import os
from wsgiref.simple_server import make_server

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.static import static_view

from accloud.finder import UserManager
from finder.requesthandler.directorySettingsHandler import DirectoryLoadSettings


def root_factory(settings):
    auth = settings['authentication']
    if auth == 'None':
        return '.resources.NoAuthenticationRoot'
    elif auth == 'standard':
        return '.resources.Root'
    else:
        raise BaseException('Error: Unknown authentication setting [{0}]'.format(auth))


def serve(**settings):
    authn_policy = AuthTktAuthenticationPolicy(
        'sosecret', callback=UserManager.groupfinder, hashalg='sha512')
    authz_policy = ACLAuthorizationPolicy()
    config = Configurator(settings=settings, root_factory=root_factory(settings))
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)

    config.include('pyramid_chameleon')
    if settings['trace']:
        config.include('pyramid_debugtoolbar')
        config.registry.settings['reload_templates'] = True

    config.registry.settings['directory_settings'] = dict()

    # load directory settings
    print('Load settings')
    DirectoryLoadSettings().load_server_settings(config.registry.settings['root_dir'], config)
    print('Adding routes')

    dir_path = r'([\w\-\_]*\/)*'
    file_basename = r'[\w\-\_\.]*'

    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('usermanagement', '/um')

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
    config.add_route('files', '/*subpath', permission='authenticatedusers')

    print('Add views')
    here = lambda p: os.path.join(os.path.abspath(os.path.dirname(__file__)), p)
    static = static_view(here('static'), use_subpath=True)
    files = static_view(
        os.path.abspath(config.registry.settings['root_dir']),
        use_subpath=True)

    config.add_view(static, route_name='static')
    config.add_view(files, route_name='files', permission='authenticatedusers')
    config.scan()
    app = config.make_wsgi_app()
    print('Creating server')
    server = make_server('127.0.0.1', settings['port'], app)
    print('Start serving on port {}'.format(settings['port']))
    server.serve_forever()
