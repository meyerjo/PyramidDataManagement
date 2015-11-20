import jsonpickle as jsonpickle
from Levenshtein._levenshtein import distance
from chameleon import PageTemplate
from contextlib import contextmanager
from pyramid.exceptions import NotFound
from pyramid.renderers import render
from pyramid.response import Response
import os
import re

from pyramid.view import view_config


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


def filter_to_dict(items, filtercriteria):
    returning_dict = dict()
    testregex = filtercriteria[0]
    for item in items:
        print(testregex)
        print(item)
        match = re.search(testregex, item)
        print(str(match))
        if match.group() in returning_dict:
            returning_dict[match.group()].append(item)
        else:
            returning_dict[match.group()] = [item]
    return returning_dict


@view_config(route_name='directory')
def directory(request):
    relative_path = os.path.join(
        request.registry.settings['root_dir'],
        request.matchdict['dir'])
    listing = os.listdir(relative_path)
    visible_items = []
    visible_items_by_extension = dict()
    invisible_items = []
    directory_settings = {'blacklist': []}
    for item in listing:
        if not item.startswith('.'):
            skipfile = False
            for rule in directory_settings['blacklist']:
                if rule == '':
                    continue
                if re.search(rule, item) is not None:
                    print(re.search(rule, item))
                    skipfile = True
                    break
            if skipfile:
                continue

            visible_items.append(item)
            filename, file_extension = os.path.splitext(item)
            if file_extension in visible_items_by_extension:
                visible_items_by_extension[file_extension].append(item)
            else:
                visible_items_by_extension[file_extension] = [item]
        else:
            invisible_items.append(item)
            if item == '.settings.json':
                with open(os.path.join(request.registry.settings['root_dir'],
                                       request.matchdict['dir'],
                                       item), "r") as myfile:
                    data = myfile.read()
                    directory_settings = jsonpickle.decode(data)
    if 'specific_filetemplates' in directory_settings:
        for (key, values) in directory_settings['specific_filetemplates'].items():
            if key in visible_items_by_extension and \
                    key in directory_settings['specific_filetemplates']:
                # TODO: make something like that parametric
                visible_items_by_extension[key] = \
                    filter_to_dict(visible_items_by_extension[key],
                                   directory_settings['specific_filetemplates'][key]['group_by'])

    visible_items_by_extension['..'] = ['..']

    if not request.matchdict['dir'] == '':
        visible_items.insert(0, '..')

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
                                <i class="fa fa-folder" tal:condition="python: extension == ''"></i>
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

    directory_entry = response(
        dir=request.matchdict['dir'],
        visible_items_by_extension=visible_items_by_extension)

    folders = visible_items_by_extension[''] if '' in visible_items_by_extension else []
    files = dict(visible_items_by_extension)
    if '' in files:
        del files['']
    html = render('template/index.pt', {'request': request,
                                        'html': directory_entry,
                                        'folders': folders,
                                        'files': files})
    return Response(html)
