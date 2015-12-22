import os

from pyramid.renderers import render
from pyramid.response import Response
from pyramid.view import (
    view_config,
)

from accloud.finder.directoryExportHandlers import PresentationExportHandler, ReportExportHandler
from accloud.finder.directoryRequestHandler import DirectoryRequestHandler
from accloud.finder.directorySettingsHandler import DirectoryLoadSettings, DirectoryCreateLocalSettings
from accloud.finder.directoryZipHandler import DirectoryZipHandler
from accloud.finder.templateHandler import TemplateHandler
from itemgrouper import ItemGrouper


class DirectoryRequest:
    def __init__(self, request):
        self.request = request
        self.logged_in = request.authenticated_userid

    def _custom_request_handler(self, relative_path, directory_settings):
        param_dict = dict(self.request.params)
        if 'presentation' in param_dict:
            return PresentationExportHandler.handle_request(self.request, relative_path, directory_settings)
        elif 'report' in param_dict:
            return ReportExportHandler.handle_request(self.request, relative_path, directory_settings)
        elif 'createlocalsettingsfile' in param_dict:
            # write the local settings file and then proceed
            DirectoryCreateLocalSettings.handle_request(self.request, relative_path, directory_settings)
            return None
        elif 'zipfile' in param_dict:
            return DirectoryZipHandler.handle_request(self.request, relative_path, directory_settings)
        else:
            return None

    @view_config(route_name='directory', permission='authenticatedusers')
    def directory(self):
        relative_path = DirectoryRequestHandler.requestfolderpath(self.request)
        listing = os.listdir(relative_path)
        relative_path = str(os.path.abspath(relative_path)).encode('string-escape')
        relative_path = relative_path.decode('string-escape')

        # load settings, and reload if necessary
        directory_settings = self.request.registry.settings['directory_settings']
        directory_settings = DirectoryLoadSettings.handle_request(self.request, relative_path, directory_settings)

        # TODO: Check whether there is a more 'clean' way to handle these specific requests
        custom_response = self._custom_request_handler(relative_path, directory_settings)
        if custom_response is not None:
            return custom_response

        visible_items_by_extension, vi, invitems = ItemGrouper().group_folder(listing, directory_settings)

        # get the folders and files
        folders = visible_items_by_extension[''] if '' in visible_items_by_extension else []
        files = dict(visible_items_by_extension)
        if '' in files:
            del files['']

        # apply specific to the items
        visible_items_by_extension = TemplateHandler().apply_templates(visible_items_by_extension, directory_settings)

        custom_directory_template_path = TemplateHandler.loadCustomTemplate(self.request, directory_settings,
                                                                            'directory_template_path',
                                                                            'template/directory.pt')

        # send it to the general directory view
        directory_entry = render(custom_directory_template_path, dict(dir=self.request.matchdict['dir'],
                                                                      visible_items_by_extension=visible_items_by_extension))

        custom_index_path = TemplateHandler.loadCustomTemplate(self.request, directory_settings, 'custom_index_path',
                                                               'template/index.pt')
        localsettingsfileexists = '.settings.json' in invitems
        index_parameter = dict(request=self.request, html=directory_entry, folders=folders, files=files,
                               localsettingsfile=localsettingsfileexists,
                               logged_in=self.request.authenticated_userid)
        return Response(render(custom_index_path, index_parameter))
