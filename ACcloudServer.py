#!/usr/bin/env python2.7
'''HTTP Server and Request Handlers to explore ACcloud experiments'''

from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from pyramid.static import static_view
from pyramid.config import Configurator
from pyramid.view import view_config
from wsgiref.simple_server import make_server
from chameleon import PageTemplate
import hoedown as md
import csv
import os


def hello_world(request):
    return Response('<body>Hello World</body>')


def csv_table(request):
    relative_path = os.path.join(
        request.registry.settings['root_dir'],
        request.matchdict['file'])

    with open(relative_path, 'r') as csv_file:
        reader = csv.reader(csv_file)
        table = PageTemplate('''<table>
            <tr tal:repeat="row table"><td tal:repeat="cell row" tal:content="cell"/></tr>
            </table>''')
        return Response(table(table=reader))

    return Response('Found csv file')


def directory(request):
    relative_path = os.path.join(
        request.registry.settings['root_dir'],
        request.matchdict['dir'])
    listing = os.listdir(relative_path)
    visible_items = list(item for item in listing if not item.startswith('.'))
    if not request.matchdict['dir'] == '':
        visible_items.insert(0, '..')
    response = PageTemplate('''
    Found dir: ${dir}
    <ul>
        <li tal:repeat="item items"><a tal:attributes="href item" tal:content="item" /></li>
    </ul>
    ''')
    return Response(response(
        dir=request.matchdict['dir'],
        items=visible_items))


def markdown(request):
    markdown_path = request.matchdict['file']
    with open(
        os.path.join(
            request.registry.settings['root_dir'],
            markdown_path), 'r') as markdown_file:
        source = markdown_file.read()
    html = md.Markdown(
        md.HtmlRenderer(md.HTML_TOC),
        md.EXT_TABLES).render(source)
    return {"request": request, "html":html}


def serve(**settings):
    config = Configurator(settings=settings)
    config.include('pyramid_chameleon')
    if settings['trace']:
        config.include('pyramid_debugtoolbar')

    here = lambda p: os.path.join(os.path.abspath(os.path.dirname(__file__)), p)
    static = static_view(here('static'), use_subpath=True)
    files = static_view(config.registry.settings['root_dir'], use_subpath=True)

    dir_path = r'([\w\-\_]*\/)*'
    file_basename = r'[\w\-\_\.]*'

    config.add_route(
        'markdown',
        '/{file:' + dir_path + file_basename + '\.md}')
    config.add_route(
        'csv',
        '/{file:' + dir_path + file_basename + '\.csv}')
    config.add_route(
        'directory',
        '/{dir:' + dir_path + '}')
    config.add_route('static', '/_static/*subpath')
    config.add_route('files', '/*subpath')

    config.add_view(
        markdown,
        route_name='markdown',
        renderer=here('static/templates/markdown.pt'))
    config.add_view(csv_table, route_name='csv')
    config.add_view(directory, route_name='directory')
    config.add_view(static, route_name='static')
    config.add_view(files, route_name='files')

    app = config.make_wsgi_app()
    print('Creating server')
    server = make_server('127.0.0.1', settings['port'], app)
    print('Start serving on port {}'.format(settings['port']))
    server.serve_forever()


if __name__ == '__main__':
    import os
    import argparse
    import webbrowser
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
            serve(**settings)
        except KeyboardInterrupt:
            pass
        except:
            pdb.post_mortem()
    else:
        serve(**settings)
