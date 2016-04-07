import logging
import os

import datetime
import jsonpickle
from chameleon import PageTemplate
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

    def _local_settings_file_exists(self):
        relative_path = DirectoryRequestHandler.requestfolderpath(self.request)
        listing = os.listdir(relative_path)
        return '.settings.json' in listing

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

        folder_descriptions = dict()
        for f in folders:
            folder_descriptions[f] = self._get_custom_directory_description(f)

        # apply specific to the items
        visible_items_by_extension = TemplateHandler().apply_templates(visible_items_by_extension, directory_settings, folder_descriptions)

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
        logger = logging.getLogger(__name__)
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
                    # TODO: how to handle this? somehow not so easy to set new get parameters for the new request
                    logger.warning('Error occured while saving the folder description: {0}'.format(str(e)))

        subreq = self.request.copy()
        subreq.method = 'GET'
        return self.request.invoke_subrequest(subreq)

    @view_config(route_name='files_comment', permission='authenticatedusers', renderer='template/index.pt')
    def file_comment_view(self):
        file = self.request.matchdict['file']
        action = self.request.matchdict['action']
        assert(action == 'comment')
        logger = logging.getLogger(__name__)
        logger.warning('Not yet implemented. Retrieval of description/comments for the given file {0}'.format(file))

        description='Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim. Donec pede justo, fringilla vel, aliquet nec, vulputate eget, arcu. In enim justo, rhoncus ut, imperdiet a, venenatis vitae, justo. Nullam dictum felis eu pede mollis pretium. Integer tincidunt. Cras dapibus. Vivamus elementum semper nisi. Aenean vulputate eleifend tellus. Aenean leo ligula, porttitor eu, consequat vitae, eleifend ac, enim. Aliquam lorem ante, dapibus in, viverra quis, feugiat a,'
        comments = [dict(person='Testperson', time='2016-04-05 00:00:00', comment='Lorem ipsum'), dict(person='Testperson', time='2016-04-05 00:00:00', comment='Lorem ipsum'), dict(person='Testperson', time='2016-04-05 00:00:00', comment='Lorem ipsum')]
        template = '''
        <script language="javascript" type="text/javascript">
          function resizeIframe(obj) {
            obj.style.height = 0.8*obj.contentWindow.document.body.scrollHeight + 'px';
          }
        </script>
        <div id='row'>
            <div class='col-sm-9'>
              <span tal:switch="python: file[-3:]">
                <span tal:case="'png'">
                    <img src='/${file}' class='col-sm-12' width="1024" height="768"/>
                </span>
                <span tal:case="default">
                    <iframe class='col-sm-12' src='/${file}' frameborder="0" scrolling="yes" onload="resizeIframe(this)"></iframe>
                </span>
              </span>
           </div>
           <div class='col-sm-3'>
              <h3>Description</h3>
              <div class='row'>
                <span tal:content="description"></span>
                <button class="btn btn-success" name="edit_description" id="edit_description">Edit description</button>
              </div>
              <span tal:condition="exists: comments">
                  <h3>Comments</h3>
                  <div class="col-sm-12" tal:repeat='comment comments'>
                      <div class="panel panel-default">
                        <div class="panel-heading">
                            <span style='font-face:bold' tal:content='comment["person"]'></span>
                            <span class='text-muted' tal:content='comment["time"]'>
                        </div>
                        <div class="panel-body" tal:content='comment["comment"]'>
                        </div><!-- /panel-body -->
                      </div><!-- /panel panel-default -->
                  </div><!-- /col-sm-5 -->
                  <div class="col-sm-12">
                    <div class="panel panel-default">
                        <div class="panel-heading">
                            <span style='font-face:bold' tal:content="logged_in"></span>
                            <span class='text-muted'></span>
                        </div>
                        <div class="panel-body">
                        <form method="post">
                            <textarea id="new_comment" name="comment"></textarea>
                            <button id="save_comment" type="submit" name="save_comment" class="btn btn-success">Save</button>
                        </form>
                        </div><!-- /panel-body -->
                      </div><!-- /panel panel-default -->
                  </div>
              </span>
           </div>
        </div>
        '''

        pt = PageTemplate(template)
        html = pt(file=file, description=description, comments=comments, logged_in=self.request.authenticated_userid)

        return dict(files=[], folders=[], pagetitle='Test',
                    request=self.request, html=html, localsettingsfile=True, logged_in=self.request.authenticated_userid)

    @view_config(route_name='files_comment', permission='authenticatedusers', renderer='template/index.pt', request_method='POST')
    def comments(self):
        file = self.request.matchdict['file']
        action = self.request.matchdict['action']
        assert(action == 'comment')
        new_comment_entry = dict(user=self.request.authenticated_userid,
                                 comment=self.request.POST['comment'],
                                 time=datetime.datetime.now(),
                                 file=file)

        new_comment_str = jsonpickle.encode(new_comment_entry)

        print('Not yet implemented add: {0} {1} to the database'.format(file, new_comment_str))

        subreq = self.request.copy()
        subreq.method = 'GET'
        return self.request.invoke_subrequest(subreq)
