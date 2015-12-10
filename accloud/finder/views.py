import os
from contextlib import contextmanager

from pyramid.exceptions import NotFound
from pyramid.renderers import render
from pyramid.response import Response
from pyramid.view import view_config

from accloud.finder.directoryExportHandlers import PresentationExportHandler, ReportExportHandler
from accloud.finder.directoryRequestHandler import DirectoryRequestHandler
from accloud.finder.directorySettingsHandler import DirectoryLoadSettings, DirectoryCreateLocalSettings
from accloud.finder.directoryZipHandler import DirectoryZipHandler
from accloud.finder.templateHandler import TemplateHandler
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


@view_config(route_name='directory')
def directory(request):
    relative_path = DirectoryRequestHandler.requestfolderpath(request)
    listing = os.listdir(relative_path)
    relative_path = str(os.path.abspath(relative_path)).encode('string-escape')
    relative_path = relative_path.decode('string-escape')

    # load settings, and reload if necessary
    directory_settings = request.registry.settings['directory_settings']
    directory_settings = DirectoryLoadSettings.handle_request(request, relative_path, directory_settings)

    # TODO: Check whether there is a more 'clean' way to handle these specific requests
    param_dict = dict(request.params)
    if 'presentation' in param_dict:
        return PresentationExportHandler.handle_request(request, relative_path, directory_settings)
    elif 'report' in param_dict:
        return ReportExportHandler.handle_request(request, relative_path, directory_settings)
    elif 'createlocalsettingsfile' in param_dict:
        # write the local settings file and then proceed
        DirectoryCreateLocalSettings.handle_request(request, relative_path, directory_settings)
    elif 'zipfile' in param_dict:
        return DirectoryZipHandler.handle_request(request, relative_path, directory_settings)

    visible_items_by_extension, vi, invitems = ItemGrouper().group_folder(listing, directory_settings)

    # get the folders and files
    folders = visible_items_by_extension[''] if '' in visible_items_by_extension else []
    files = dict(visible_items_by_extension)
    if '' in files:
        del files['']

    # apply specific to the items
    visible_items_by_extension = TemplateHandler().apply_templates(visible_items_by_extension, directory_settings)

    custom_directory_template_path = TemplateHandler.loadCustomTemplate(request, directory_settings,
                                                                        'directory_template_path',
                                                                        'template/directory.pt')

    # send it to the general directory view
    directory_entry = render(custom_directory_template_path, dict(dir=request.matchdict['dir'],
                                                                  visible_items_by_extension=visible_items_by_extension))

    custom_index_path = TemplateHandler.loadCustomTemplate(request, directory_settings, 'custom_index_path',
                                                           'template/index.pt')
    localsettingsfileexists = '.settings.json' in invitems
    index_parameter = dict(request=request, html=directory_entry, folders=folders, files=files,
                           localsettingsfile=localsettingsfileexists)
    return Response(render(custom_index_path, index_parameter))
