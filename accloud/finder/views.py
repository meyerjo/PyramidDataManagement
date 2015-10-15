from chameleon import PageTemplate
from contextlib import contextmanager
from pyramid.response import Response
import csv
import hoedown
import os

@contextmanager
def open_resource(filename, mode="r"):
    try:
        f = open(filename, mode)
    except IOError:
        raise NotFound
    else:
        try:
            yield f
        finally:
            f.close()

def csv_table(request):
    relative_path = os.path.join(
        request.registry.settings['root_dir'],
        request.matchdict['file'])

    with open_resource(relative_path) as csv_file:
        reader = csv.reader(csv_file)
        table = PageTemplate('''<table>
            <tr tal:repeat="row table"><td tal:repeat="cell row" tal:content="cell"/></tr>
            </table>''')
        return Response(table(table=reader))


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
        items=sorted(visible_items)))


def markdown(request):
    markdown_path = os.path.join(
            request.registry.settings['root_dir'], request.matchdict['file'])
    with open_resource(markdown_path) as markdown_file:
        source = markdown_file.read()
        html = hoedown.Markdown(
            hoedown.HtmlRenderer(hoedown.HTML_TOC),
            hoedown.EXT_TABLES).render(source)
        return {"request": request, "html":html}
