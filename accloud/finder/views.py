from chameleon import PageTemplate
from contextlib import contextmanager

from pyramid.exceptions import NotFound
from pyramid.response import Response
import csv
import hoedown
import os

ignore_fileextensions =  ['.asv']

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

def filter_to_dict(items, differing_characters):
    returning_dict = dict()
    for item in items:
        if item[:differing_characters] in returning_dict:
            returning_dict[item[:differing_characters]].append(item)
        else:
            returning_dict[item[:differing_characters]] = [item]
    return returning_dict




def directory(request):
    relative_path = os.path.join(
        request.registry.settings['root_dir'],
        request.matchdict['dir'])
    listing = os.listdir(relative_path)
    visible_items = []
    visible_items_by_extension = dict()
    invisible_items = []
    for item in listing:
        if not item.startswith('.'):
            visible_items.append(item)
            filename, file_extension = os.path.splitext(item)
            if file_extension in ignore_fileextensions:
                continue
            if file_extension in visible_items_by_extension:
                visible_items_by_extension[file_extension].append(item)
            else:
                visible_items_by_extension[file_extension] = [item]
        else:
            invisible_items.append(item)
    if '.png' in visible_items_by_extension:
        visible_items_by_extension['.png'] = filter_to_dict(visible_items_by_extension['.png'], 4)

    if not request.matchdict['dir'] == '':
        visible_items.insert(0, '..')
    # response = PageTemplate('''
    # Found dir: ${dir}
    # <ul>
    #     <li tal:repeat="item items"><a tal:attributes="href item" tal:content="item" /></li>
    # </ul>
    # ''')
    response = PageTemplate('''
    Found dir: ${dir}
    <ul metal:define-macro="filter_depth">
        <li tal:repeat="(key, values) sorted(visible_items_by_extension.items())">
            <div tal:condition="python: key.startswith('.') or not key">
                <span tal:define="global extension key;"></span>
            </div>
            <span tal:content="key"></span>
            <ul tal:condition="python: type(values) is not dict">
                <li tal:repeat="value values">
                    <ul tal:condition="python: type(value) is dict" metal:use-macro="template.macro['filter_depth']"/>
                    <span tal:condition="python: type(value) is not dict">
                        <div tal:switch="extension">
                            <div tal:case="'.png'">
                                <img tal:attributes="src value; alt value;"/>
                                <tal:span tal:content="value"/>
                            </div>
                            <div tal:case="default">
                                <a tal:attributes="href value" tal:content="value"/>
                            </div>
                        </div>
                    </span>
                </li>
            </ul>
            <div tal:condition="python: type(values) is dict" tal:define="visible_items_by_extension values">
                <ul metal:use-macro="template.macros['filter_depth']"></ul>
            </div>
        </li>
    </ul>
    ''')
    print(visible_items_by_extension)
    return Response(response(
        dir=request.matchdict['dir'],
        visible_items_by_extension=visible_items_by_extension))


def markdown(request):
    markdown_path = os.path.join(
            request.registry.settings['root_dir'], request.matchdict['file'])
    with open_resource(markdown_path) as markdown_file:
        source = markdown_file.read()
        html = hoedown.Markdown(
            hoedown.HtmlRenderer(hoedown.HTML_TOC_TREE),
            hoedown.EXT_TABLES).render(source)
        return {"request": request, "html":html}
