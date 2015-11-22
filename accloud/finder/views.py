import jsonpickle as jsonpickle
import math
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
    assert (len(filtercriteria) >= 1)
    if len(filtercriteria) > 1:
        print('WARNING: You specified more than one group criteria. Currently only one is supported.')
    returning_dict = dict()
    testregex = filtercriteria[0]
    for item in items:
        match = re.search(testregex, item)
        if match is None:
            print('Couldnt group the following item, because the regex failed {0} {1}'.format(item, testregex))
            continue
        if match.group() in returning_dict:
            returning_dict[match.group()].append(item)
        else:
            returning_dict[match.group()] = [item]
    return returning_dict


def split_into_rows(input, items_per_row):
    assert (items_per_row >= 1)
    if isinstance(input, list):
        rows = []
        tmp_row = []
        for item in input:
            tmp_row.append(item)
            if len(tmp_row) == items_per_row:
                rows.append(tmp_row)
                tmp_row = []
        if tmp_row is not []:
            rows.append(tmp_row)
        return rows
    elif isinstance(input, dict):
        for (key, value) in input.items():
            input[key] = split_into_rows(value, items_per_row)
        return input
    else:
        print('Something went wrong')
        return input


def load_directory_settings(directory, request):
    if directory in request.registry.settings['directory_settings']:
        directory_settings = request.registry.settings['directory_settings'][directory]
        if 'reload' in request.registry.settings['directory_settings'][directory]:
            reload_templates = request.registry.settings['directory_settings'][directory]['reload']
            if reload_templates:
                with open(directory_settings['path'], "r") as myfile:
                    data = myfile.read()
                    directory_settings = jsonpickle.decode(data)
                    return directory_settings
            return directory_settings
        return directory_settings
    return dict()


@view_config(route_name='directory')
def directory(request):
    relative_path = os.path.join(
        request.registry.settings['root_dir'],
        request.matchdict['dir'])
    listing = os.listdir(relative_path)
    visible_items = []
    visible_items_by_extension = dict()
    invisible_items = []
    relative_path = str(os.path.abspath(relative_path)).encode('string-escape')
    relative_path = relative_path.decode('string-escape')

    # load settings, and reload if necessary
    directory_settings = load_directory_settings(relative_path, request)

    # iterate over all files
    for item in listing:
        filename, file_extension = os.path.splitext(item)
        if not item.startswith('.'):
            skipfile = False
            if 'blacklist' in directory_settings:
                for rule in directory_settings['blacklist']:
                    if rule == '':
                        continue
                    if re.search(rule, item) is not None:
                        skipfile = True
                        break
                if skipfile:
                    continue
            visible_items.append(item)
            if file_extension in visible_items_by_extension:
                visible_items_by_extension[file_extension].append(item)
            else:
                visible_items_by_extension[file_extension] = [item]
        else:
            invisible_items.append(item)

    # apply templates
    if 'specific_filetemplates' in directory_settings:
        for (key, values) in directory_settings['specific_filetemplates'].items():
            if key in visible_items_by_extension and \
                            key in directory_settings['specific_filetemplates']:
                # TODO: make this more readable / compact
                try:
                    visible_items_by_extension[key] = \
                        filter_to_dict(visible_items_by_extension[key],
                                       directory_settings['specific_filetemplates'][key]['group_by'])
                except Exception as e:
                    print(e.message)
                elements_per_row = directory_settings['specific_filetemplates'][key]['elements_per_row']
                column_width = int(math.ceil(12 / elements_per_row))
                specific_template = PageTemplate(directory_settings['specific_filetemplates'][key]['template'])
                visible_items_by_extension[key] = split_into_rows(visible_items_by_extension[key], elements_per_row)
                html = specific_template(grouped_files=visible_items_by_extension[key],
                                         columnwidth=column_width)
                visible_items_by_extension[key] = [html]

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
                        <div tal:condition="python: value.startswith('<')">
                            ${structure: value}
                        </div>
                        <div tal:condition="python: not value.startswith('<')">
                            <i class="fa fa-file"  tal:condition="python: extension != ''"></i>
                            <i class="fa fa-folder" tal:condition="python: extension == ''"></i>
                            <a tal:attributes="href value" tal:content="value"/>
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
