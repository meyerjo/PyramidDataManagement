import csv
import hoedown
import os

from chameleon import PageTemplate
from pyramid.renderers import render
from pyramid.response import Response
from pyramid.view import view_config

from accloud.finder.MatlabParser import MatlabParser
from accloud.finder.csvHandler import CSVHandler
from accloud.finder.directoryRequestHandler import DirectoryRequestHandler
from accloud.finder.directorySettingsHandler import DirectoryUpdateLocalSettings
from accloud.finder.fileHandler import open_resource


class FileSpecificViews:
    def __init__(self, request):
        self.request = request
        self.logged_in = request.authenticated_userid

        self._keyDicthtml = PageTemplate('''
            <tr tal:repeat="(key, values) keydictionaries.items()" class="border_bottom">
                <th tal:content="key"></th>
                <span tal:condition="python: not isinstance(values, dict)">
                    <td tal:attributes="id values[3]">
                        <span tal:content="values[1]"/>
                        <button class="btn btn-success" tal:condition="python: not values[2]">Expand</button>
                    </td>
                </span>
                <td tal:condition="python: isinstance(values, dict)">
                    <table metal:define-macro="filter_depth" >
                        <tr tal:repeat="(subkeys, subvalues) values.items()">
                            <th tal:content="subkeys" tal:condition="python: subkeys is not []"/>
                            <td tal:condition="python: not isinstance(subvalues, dict)" tal:attributes="id subvalues[3]">
                                <span tal:content="subvalues[1]"/>
                                <button class="btn btn-success" tal:condition="python: not subvalues[2]">Expand</button>
                            </td>
                            <td tal:condition="python: isinstance(subvalues, dict)">
                                <table tal:define="values subvalues"
                                       metal:use-macro="template.macros['filter_depth']"/>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        ''')

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
            keys_html = self._keyDicthtml(keydictionaries=keydict)
            return Response(keys_html)

        table = PageTemplate('''
                <script src="https://code.jquery.com/jquery-2.1.4.min.js" type="text/javascript"></script>
                <script>
                    $(document).ready(function() {
                        $("button").on('click', function() {
                            parent_id = $(this).parent().attr("id");
                            parent = $(this).closest('tr');
                            $.ajax({
                                url: window.location.href + '/' + parent_id,
                                method: 'GET'
                            }).done(function(data) {
                                $(parent).replaceWith(data);
                            });
                        });
                    });
                </script>
                <style>
                tr.border_bottom td {
                  border-bottom:1pt solid black;
                }
                tr.border_bottom th {
                  border-bottom:1pt solid black;
                }
                </style>
                <table class="table table-striped table-bordered table-condensed">
                    <tr>
                        <th tal:repeat="title matlabheaders" tal:content="title"/>
                    </tr>
                    ${structure: rows}
                </table>''')

        matlabheaders = ['Keys', 'Values']
        keydict = MatlabParser(matlabpath).retrieve_structure()
        keys_html = self._keyDicthtml(keydictionaries=keydict)
        table_html = table(matlabheaders=matlabheaders, rows=keys_html)
        return dict(request=self.request, html=table_html, files=dict(), folders=['.', '..'],
                    logged_in=self.request.authenticated_userid)
