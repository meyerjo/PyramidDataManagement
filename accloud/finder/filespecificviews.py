import csv
import hoedown
import os

from chameleon import PageTemplate
from pyramid.renderers import render
from pyramid.response import Response
from pyramid.view import view_config

from finder.requesthandler.MatlabParser import MatlabParser
from finder.requesthandler.csvHandler import CSVHandler
from finder.requesthandler.directoryRequestHandler import DirectoryRequestHandler
from finder.requesthandler.directorySettingsHandler import DirectoryUpdateLocalSettings
from finder.requesthandler.fileHandler import open_resource


class FileSpecificViews:
    def __init__(self, request):
        self.request = request
        self.logged_in = request.authenticated_userid

    @view_config(route_name='csv', renderer='template/index.pt', permission='authenticatedusers')
    @view_config(route_name='csv_delimiter', renderer='template/index.pt', permission='authenticatedusers')
    def csv_table(self):
        relative_path = DirectoryRequestHandler.requestfilepath(self.request)
        delimit = CSVHandler.getdelimiter(relative_path, self.request.matchdict)

        with open_resource(relative_path) as csv_file:
            reader = csv.reader(csv_file, delimiter=delimit)
            table = PageTemplate('''<table class="table table-striped table-bordered table-condensed">
                <tr tal:repeat="row table"><td tal:repeat="cell row" tal:content="cell"/></tr>
                </table>''')
            table_html = table(table=reader)
        return dict(request=self.request, html=table_html, files=dict(), folders=['.', '..'],
                    logged_in=self.request.authenticated_userid)

    @view_config(route_name='markdown', renderer='template/index.pt', permission='authenticatedusers')
    def markdown(self):
        markdown_path = DirectoryRequestHandler.requestfilepath(self.request)
        with open_resource(markdown_path) as markdown_file:
            source = markdown_file.read()
            source = str(source)
            html = hoedown.Markdown(
                hoedown.HtmlRenderer(hoedown.HTML_TOC_TREE),
                hoedown.EXT_TABLES).render(source)
            html = render('template/markdown.pt', {"request": self.request, "html": html})
        return dict(request=self.request, html=html, files=dict(), folders=['.', '..'],
                    logged_in=self.request.authenticated_userid)

    @view_config(route_name='matlab', renderer='template/index.pt', permission='authenticatedusers')
    def matlab(self):
        matlab_path = DirectoryRequestHandler.requestfilepath(self.request)

        with open_resource(matlab_path) as matlab_file:
            source = matlab_file.read()
            matlab_html = render('template/matlab.pt', {"request": self.request, "html": source})
        return dict(request=self.request, html=matlab_html, files=dict(), folders=['.', '..'],
                    logged_in=self.request.authenticated_userid)

    @view_config(route_name='jsonviewer', renderer='template/index.pt', permission='authenticatedusers')
    @view_config(route_name='jsonviewer_plain', renderer='json', permission='authenticatedusers')
    def jsonview(self):
        """
        Returns the json file either in a formatted way or as plain text
        :return:
        """
        jsonpath = DirectoryRequestHandler.requestfilepath(self.request)
        if not os.path.exists(jsonpath):
            return dict(request=self.request, html='', files=dict(), folders=['.', '..'])

        params_json = dict(self.request.params)
        if 'updatelocalsettingsfile' in params_json and 'newsettings' in params_json:
            return DirectoryUpdateLocalSettings.handle_request(self.request, jsonpath, None)

        with open_resource(jsonpath) as json:
            source = json.read()
            if self.request.matched_route.name == 'jsonviewer_plain':
                return source

            json_html = render('template/json_view.pt', dict(request=self.request,
                                                             jsonencoded=source,
                                                             filename=self.request.matchdict['file']))
            return dict(request=self.request, html=json_html, files=dict(), folders=['.', '..'],
                        logged_in=self.request.authenticated_userid)

    @view_config(route_name='matlabfileviewer', renderer='template/index.pt', permission='authenticatedusers')
    @view_config(route_name='matlabfileviewer_subpath', permission='authenticatedusers')
    def matlabreader(self):
        """
        Read matlab files
        :return:
        """
        matlabpath = DirectoryRequestHandler.requestfilepath(self.request)
        if self.request.matched_route.name == 'matlabfileviewer_subpath':
            subkeypath = self.request.matchdict['subkeypath']
            split_keys = subkeypath.split('&')
            keydict = MatlabParser(matlabpath).specific_element(split_keys)
            keydict = {split_keys[-1]: keydict}
            return Response(render('template/matfiles_overview.pt', dict(keydictionaries=keydict)))

        matlabheaders = ['Keys', 'Values']
        keydict = MatlabParser(matlabpath).retrieve_structure()
        keys_html = render('template/matfiles_overview.pt',
                           dict(keydictionaries=keydict))
        table_html = render('template/matfiles.pt',
                            dict(matlabheaders=matlabheaders, rows=keys_html))
        return dict(request=self.request, html=table_html, files=dict(), folders=['.', '..'],
                    logged_in=self.request.authenticated_userid)
