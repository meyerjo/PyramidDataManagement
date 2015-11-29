import inspect
import math
import os
import time
from contextlib import contextmanager

import jsonpickle as jsonpickle
import pdfkit
from chameleon import PageTemplate
from markdown import markdown
from pyramid.exceptions import NotFound
from pyramid.renderers import render
from pyramid.response import Response
from pyramid.view import view_config

from accloud.finder.markdownexport import MarkdownExport, PresentationMarkdownExport
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


def load_directory_settings(directorypath, directorysettings):
    """
    Load the directory settings for the specific directory. Checks if it is indicated that a reload is required.
    :param directorypath: Path of the folder, which should load the files
    :param directorysettings: Dictionary with the specific directory settings
    :return:
    """
    if directorypath in directorysettings:
        directory_settings = directorysettings[directorypath]
        if 'reload' in directorysettings[directorypath]:
            reload_templates = directorysettings[directorypath]['reload']
            if reload_templates:
                if os.path.exists(directory_settings['path']):
                    with open(directory_settings['path'], "r") as myfile:
                        data = myfile.read()
                        directory_settings = jsonpickle.decode(data)
                        return directory_settings
            return directory_settings
        return directory_settings
    else:
        # check if the parent folder has some marked settings
        previous_folder = os.path.abspath(directorypath + '/../')
        previous_folder = previous_folder.encode('string-escape')
        previous_folder = previous_folder.decode('string-escape')
        return load_directory_settings(previous_folder, directorysettings)


def apply_specific_templates(filenames, extension_specific):
    """
    Applies the specific templates which are set in the directory_settings to the list of files
    :param filenames:
    :param extension_specific:
    :return:
    """
    elements_per_row = extension_specific['elements_per_row']
    column_width = int(math.ceil(12 / elements_per_row))

    specific_template = PageTemplate(extension_specific['template'])
    html = specific_template(grouped_files=filenames, columnwidth=column_width)
    return html


def handle_presentation_request(request, relative_path, directory_settings):
    """
    Handles the request to present a folder or a specific filetype in a folder as a markdown based presentation
    :param request:
    :param relative_path:
    :param directory_settings:
    :return:
    """
    presmd = PresentationMarkdownExport(request)
    specific_filetype = None
    if 'specific' in dict(request.params):
        specific_filetype = request.params['specific']
    output = '# Presentation\n{0}\n---\n'.format(time.strftime('%d.%m.%Y'))
    output += presmd.export_folder(relative_path, directory_settings, specific_filetype)
    htmloutput = render('template/markdown_presentation.pt', dict(markdown=output))
    return Response(htmloutput)


def handle_report_request(request, relative_path, directory_settings):
    """
    Handles the PDF requests
    :param request:
    :param relative_path:
    :param directory_settings:
    :return:
    """
    mdexport = MarkdownExport(request)
    specific_filetype = None
    if 'specific' in dict(request.params):
        specific_filetype = request.params['specific']
    output = mdexport.export_folder(relative_path, directory_settings, specific_filetype)
    html_text = markdown(output, output_format='html4')
    # TODO: fix this Path problem
    config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
    # TODO: replace by mkdtemp
    if not os.path.exists(relative_path + '/.temp/'):
        os.mkdir(relative_path + '/.temp/')
    pdfkit.from_string(html_text, relative_path + '/.temp/report.pdf', configuration=config)
    with open(relative_path + '/.temp/report.pdf', 'rb') as report:
        return Response(body=report.read(), content_type='application/pdf')


def write_local_settings_file(request, directory_settings):
    """
    Creates the local settings file for the corresponding directory
    :param request:
    :param directory_settings:
    :return:
    """
    relative_path = os.path.join(
        request.registry.settings['root_dir'],
        request.matchdict['dir'])
    try:
        with open(relative_path + '/.settings.json', 'w') as settings_file:
            settings_file.write(jsonpickle.encode(directory_settings, unpicklable=False))
        return None
    except IOError as e:
        return e.message


@view_config(route_name='directory')
def directory(request):
    relative_path = os.path.join(
        request.registry.settings['root_dir'],
        request.matchdict['dir'])
    listing = os.listdir(relative_path)
    relative_path = str(os.path.abspath(relative_path)).encode('string-escape')
    relative_path = relative_path.decode('string-escape')

    # load settings, and reload if necessary
    directory_settings = load_directory_settings(relative_path, request.registry.settings['directory_settings'])

    param_dict = dict(request.params)
    if 'presentation' in param_dict:
        return handle_presentation_request(request, relative_path, directory_settings)
    elif 'report' in param_dict:
        return handle_report_request(request, relative_path, directory_settings)
    elif 'createlocalsettingsfile' in param_dict:
        # write the local settings file and then proceed
        write_local_settings_file(request, directory_settings)

    itemgrouper = ItemGrouper()
    visible_items_by_extension = itemgrouper.group_folder(listing, directory_settings)

    # get the folders and files
    folders = visible_items_by_extension[''] if '' in visible_items_by_extension else []
    files = dict(visible_items_by_extension)
    if '' in files:
        del files['']

    # apply specific to the items
    for (extension, filenames) in visible_items_by_extension.items():
        if 'specific_filetemplates' in directory_settings:
            if extension in directory_settings['specific_filetemplates']:
                extension_specific = directory_settings['specific_filetemplates'][extension]
                html = apply_specific_templates(filenames, extension_specific)
                visible_items_by_extension[extension] = [html]
            elif extension != '' and not extension == '..':
                if 'file_template' in directory_settings:
                    file_template = PageTemplate(directory_settings['file_template'])
                    tmp = [file_template(item=file) for file in filenames]
                    visible_items_by_extension[extension] = tmp
            else:
                if 'folder_template' in directory_settings:
                    folder_template = PageTemplate(directory_settings['folder_template'])
                    tmp = [folder_template(item=file) for file in filenames]
                    visible_items_by_extension[extension] = tmp

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
