import os

import jsonpickle
from pyramid.renderers import render
from pyramid.response import Response
from pyramid.view import (
    view_config,
)
from webob.multidict import MultiDict

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

    def _get_custom_directory_description(self, subfolder=None):
        relative_path = DirectoryRequestHandler.requestfolderpath(self.request)
        if subfolder is None:
            description_file = '{0}.description.json'.format(
                relative_path if relative_path.endswith('/') else relative_path + '/')
        else:
            description_file = '{0}{1}/.description.json'.format(
                relative_path if relative_path.endswith('/') else relative_path + '/', subfolder)
        try:
            with open(description_file) as f:
                str_file = f.read()
                description = jsonpickle.decode(str_file)
        except BaseException as e:
            print(str(e))
            description = {'longdescription': '', 'shortdescription': ''}
        return description

    @view_config(route_name='directory', permission='authenticatedusers', request_method='GET')
    def directory(self):
        # TODO: load the description files
        relative_path = DirectoryRequestHandler.requestfolderpath(self.request)
        listing = os.listdir(relative_path)
        relative_path = str(os.path.abspath(relative_path)).encode('string-escape')
        relative_path = relative_path.decode('string-escape')

        # load settings, and reload if necessary
        directory_settings = self.request.registry.settings['directory_settings']
        directory_settings = DirectoryLoadSettings.handle_request(self.request, relative_path, directory_settings)

        # load custom description
        description = self._get_custom_directory_description()

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

        testdict = dict()
        for f in folders:
            testdict[f] = self._get_custom_directory_description(f)
        print(testdict)

        # apply specific to the items
        visible_items_by_extension = TemplateHandler().apply_templates(visible_items_by_extension, directory_settings)

        custom_directory_template_path = TemplateHandler.loadCustomTemplate(self.request, directory_settings,
                                                                            'directory_template_path',
                                                                            'template/directory.pt')

        # send it to the general directory view
        directory_entry = render(custom_directory_template_path, dict(dir=self.request.matchdict['dir'],
                                                                      visible_items_by_extension=visible_items_by_extension,
                                                                      description=description,
                                                                      request=self.request))

        custom_index_path = TemplateHandler.loadCustomTemplate(self.request, directory_settings, 'custom_index_path',
                                                               'template/index.pt')
        localsettingsfileexists = '.settings.json' in invitems
        index_parameter = dict(request=self.request, html=directory_entry, folders=folders, files=files,
                               localsettingsfile=localsettingsfileexists,
                               logged_in=self.request.authenticated_userid)
        return Response(render(custom_index_path, index_parameter))

    @view_config(route_name='directory', permission='authenticatedusers', request_method='POST')
    def directory_config(self):
        if 'save_target' in self.request.POST:
            description_obj = {}
            if 'shortdescription' in self.request.POST and 'longdescription' in self.request.POST:
                description_obj['shortdescription'] = self.request.POST['shortdescription']
                description_obj['longdescription'] = self.request.POST['longdescription']
                try:
                    relative_path = DirectoryRequestHandler.requestfolderpath(self.request)
                    relative_path = relative_path if relative_path.endswith('/') else relative_path + '/'
                    save_path = '{0}.description.json'.format(relative_path)
                    # Always overwrite the old description file. Perhaps we should be less strict
                    with open(save_path, 'w') as json_file:
                        json_file.write(jsonpickle.encode(description_obj))
                except BaseException as e:
                    # TODO: how to handle this? somehow not so easy to set new get parameters
                    print(str(e))

        subreq = self.request.copy()
        subreq.method = 'GET'
        return self.request.invoke_subrequest(subreq)
