import inspect
import math
import os
import re
from contextlib import contextmanager

import jsonpickle as jsonpickle
from chameleon import PageTemplate
from pyramid.exceptions import NotFound
from pyramid.renderers import render
from pyramid.response import Response
from pyramid.view import view_config

from itemgrouper import ItemGrouper


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


def apply_filter_to_items(items, filter):
    """
    Gets a list of string items and a list of filtercriteria consisting of regular_expressions and filters them into a dictionary
    :param items: list of strings
    :param filter: list of regular expressions
    :return: filtered dictionary
    """
    assert (isinstance(filter, str) or isinstance(filter, unicode))
    returning_dict = dict()
    for item in items:
        match = re.search(filter, item)
        if match is None:
            print('Couldn\'t group the following item, because the regex failed {0} {1}'.format(item, filter))
            continue
        if match.group() in returning_dict:
            returning_dict[match.group()].append(item)
        else:
            returning_dict[match.group()] = [item]
    return returning_dict


def filter_to_dict(items, filtercriteria):
    assert (len(filtercriteria) >= 1)
    returning_dict = dict()
    if isinstance(items, list):
        returning_dict = apply_filter_to_items(items, str(filtercriteria[0]))
    if len(filtercriteria) == 1:
        return returning_dict

    for (key, values) in returning_dict.items():
        returning_dict[key] = filter_to_dict(values, filtercriteria[1:])
    return returning_dict



def split_into_rows(input, items_per_row):
    assert (items_per_row >= 1)
    if isinstance(input, list):
        # TODO: let the user decide which method to use
        grouping_method = 'numerical'
        grouper = ItemGrouper()
        return grouper.group(input, items_per_row, grouping_method)
    elif isinstance(input, dict):
        for (key, value) in input.items():
            input[key] = split_into_rows(value, items_per_row)
        return input
    else:
        print('Something went wrong. The type of the input isn\'t a dict or a list. {0}'.format(str(type(input))))
        return input


def load_directory_settings(directory, request):
    """
    Load the directory settings for the specific directory. Checks if it is indicated that a reload is required.
    :param directory:
    :param request:
    :return:
    """
    if directory in request.registry.settings['directory_settings']:
        directory_settings = request.registry.settings['directory_settings'][directory]
        if 'reload' in request.registry.settings['directory_settings'][directory]:
            reload_templates = request.registry.settings['directory_settings'][directory]['reload']
            if reload_templates:
                if os.path.exists(directory_settings['path']):
                    with open(directory_settings['path'], "r") as myfile:
                        data = myfile.read()
                        directory_settings = jsonpickle.decode(data)
                        return directory_settings
            return directory_settings
        return directory_settings
    return dict()


def reorganize_files(listing, blacklist=[]):
    visible_items_by_extension = dict()
    visible_items = []
    invisible_items = []
    for item in listing:
        filename, file_extension = os.path.splitext(item)
        if not item.startswith('.'):
            skipfile = False
            for rule in blacklist:
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
    return visible_items_by_extension, visible_items, invisible_items


@view_config(route_name='directory')
def directory(request):
    relative_path = os.path.join(
        request.registry.settings['root_dir'],
        request.matchdict['dir'])
    listing = os.listdir(relative_path)
    relative_path = str(os.path.abspath(relative_path)).encode('string-escape')
    relative_path = relative_path.decode('string-escape')

    # load settings, and reload if necessary
    directory_settings = load_directory_settings(relative_path, request)

    # restructure files and split them according to their fileextension
    if 'blacklist' in directory_settings:
        visible_items_by_extension, visible_items, invisible_items = reorganize_files(listing, directory_settings['blacklist'])
    else:
        visible_items_by_extension, visible_items, invisible_items = reorganize_files(listing)

    # get the folders and files
    folders = visible_items_by_extension[''] if '' in visible_items_by_extension else []
    files = dict(visible_items_by_extension)
    if '' in files:
        del files['']
    visible_items_by_extension['..'] = ['..']

    # apply templates
    errors = []
    for (extension, filenames) in visible_items_by_extension.items():
        if 'specific_filetemplates' in directory_settings:
            if extension in directory_settings['specific_filetemplates']:
                extension_specific = directory_settings['specific_filetemplates'][extension]
                # TODO: make this more readable / compact
                try:
                    visible_items_by_extension[extension] = \
                        filter_to_dict(filenames, extension_specific['group_by'])
                except Exception as e:
                    errors.append(e.message)
                    print(e.message)
                elements_per_row = extension_specific['elements_per_row']
                column_width = int(math.ceil(12 / elements_per_row))

                specific_template = PageTemplate(extension_specific['template'])
                visible_items_by_extension[extension] = split_into_rows(visible_items_by_extension[extension],
                                                                        elements_per_row)
                html = specific_template(grouped_files=visible_items_by_extension[extension],
                                         columnwidth=column_width)
                visible_items_by_extension[extension] = [html]
            elif extension != '' and not extension == '..':
                # TODO: use folder_template as well
                if 'file_template' in directory_settings:
                    file_template = PageTemplate(directory_settings['file_template'])
                    tmp = [file_template(item=file) for file in filenames]
                    visible_items_by_extension[extension] = tmp
            else:
                if 'folder_template' in directory_settings:
                    folder_template = PageTemplate(directory_settings['folder_template'])
                    tmp = [folder_template(item=file) for file in filenames]
                    visible_items_by_extension[extension] = tmp

    if not request.matchdict['dir'] == '':
        visible_items.insert(0, '..')

    directory_entry = render('template/directory.pt',
                             {'dir': request.matchdict['dir'],
                              'visible_items_by_extension': visible_items_by_extension})

    # TODO: load the directory script dynamically
    script_folder = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    # print os.path.exists(script_folder + '/template/directory.pt')

    html = render('template/index.pt', {'request': request,
                                        'html': directory_entry,
                                        'folders': folders,
                                        'files': files})
    return Response(html)
