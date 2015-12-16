import csv
import hoedown
import os
import shutil
from contextlib import contextmanager
import HTMLParser

import jsonpickle
from chameleon import PageTemplate
from h5py import File
from pyramid.exceptions import NotFound
from pyramid.renderers import render
from pyramid.response import Response
from pyramid.view import view_config

from accloud.finder.MatlabParser import MatlabParser
from accloud.finder.directoryRequestHandler import DirectoryRequestHandler
from accloud.finder.directorySettingsHandler import DirectoryUpdateLocalSettings


class filespecifivviews:
    def __init__(self, request):
        self.request = request

    @contextmanager
    def open_resource(self, filename, mode="r"):
        try:
            f = open(filename, mode)
        except IOError:
            raise NotFound
        else:
            try:
                yield f
            finally:
                f.close()

    def _detect_csv_delimiter(self, text, possible_delimiter=None):
        if not possible_delimiter:
            possible_delimiter = ['\t', ',', ';', ' ']
        min_delimiter = 0
        delimit = possible_delimiter[0]
        for delimiter in possible_delimiter:
            count = text.count(delimiter)
            if count > min_delimiter:
                delimit = delimiter
                min_delimiter = count
        return delimit

    @view_config(route_name='csv', renderer='template/index.pt')
    @view_config(route_name='csv_delimiter', renderer='template/index.pt')
    def csv_table(self):
        relative_path = DirectoryRequestHandler.requestfilepath(self.request)
        auto_detect_delimiter = False
        if 'delimiter' in self.request.matchdict:
            delimit = str(self.request.matchdict['delimiter'])
            if delimit in ['tab', '/t']:
                delimit = str('\t')
            elif delimit == 'space':
                delimit = str(' ')
            elif delimit == 'auto':
                auto_detect_delimiter = True
                delimit = str(',')
        else:
            auto_detect_delimiter = True
            delimit = str(',')

        if auto_detect_delimiter:
            with self.open_resource(relative_path) as csv_file:
                possible_delimiters = ['\t', ',', ';', ' ']
                delimit = self._detect_csv_delimiter(csv_file.read(), possible_delimiters)

        with self.open_resource(relative_path) as csv_file:
            reader = csv.reader(csv_file, delimiter=delimit)
            table = PageTemplate('''<table class="table table-striped table-bordered table-condensed">
                <tr tal:repeat="row table"><td tal:repeat="cell row" tal:content="cell"/></tr>
                </table>''')
            table_html = table(table=reader)
        return dict(request=self.request, html=table_html, files=dict(), folders=['.', '..'])

    @view_config(route_name='markdown', renderer='template/index.pt')
    def markdown(self):
        markdown_path = DirectoryRequestHandler.requestfilepath(self.request)
        with self.open_resource(markdown_path) as markdown_file:
            source = markdown_file.read()
            source = str(source)
            html = hoedown.Markdown(
                hoedown.HtmlRenderer(hoedown.HTML_TOC_TREE),
                hoedown.EXT_TABLES).render(source)
            html = render('template/markdown.pt', {"request": self.request, "html": html})
        return dict(request=self.request, html=html, files=dict(), folders=['.', '..'])

    @view_config(route_name='matlab', renderer='template/index.pt')
    def matlab(self):
        matlab_path = DirectoryRequestHandler.requestfilepath(self.request)

        with self.open_resource(matlab_path) as matlab_file:
            source = matlab_file.read()
            matlab_html = render('template/matlab.pt', {"request": self.request, "html": source})
        return dict(request=self.request, html=matlab_html, files=dict(), folders=['.', '..'])

    @view_config(route_name='jsonviewer', renderer='template/index.pt')
    def jsonview(self):
        jsonpath = DirectoryRequestHandler.requestfilepath(self.request)
        if not os.path.exists(jsonpath):
            return dict(request=self.request, html='', files=dict(), folders=['.', '..'])

        params_json = dict(self.request.params)
        if 'updatelocalsettingsfile' in params_json and 'newsettings' in params_json:
            return DirectoryUpdateLocalSettings.handle_request(self.request, jsonpath, None)

        with self.open_resource(jsonpath) as json:
            source = json.read()
            json_html = render('template/json_view.pt', dict(request=self.request,
                                                             jsonencoded=source,
                                                             filename=self.request.matchdict['file']))
            return dict(request=self.request, html=json_html, files=dict(), folders=['.', '..'])

    @view_config(route_name='jsonviewer_plain', renderer='json')
    def json_plain(self):
        jsonpath = DirectoryRequestHandler.requestfilepath(self.request)
        with self.open_resource(jsonpath) as file:
            return file.read()


    @view_config(route_name='matlabfileviewer')
    def matlabreader(self):
        matlabpath = DirectoryRequestHandler.requestfilepath(self.request)
        print(MatlabParser(matlabpath).specific_element([u'vmrk', u'y']))
        table = PageTemplate('''
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
                    <tr tal:repeat="(key, values) keydictionaries.items()" class="border_bottom">
                        <th tal:content="key"></th>
                        <td tal:condition="python: not isinstance(values, dict)">
                            <td tal:content="values[0]"/>
                            <td tal:content="values[1]"/>
                        </td>
                        <td tal:condition="python: isinstance(values, dict)">
                            <table metal:define-macro="filter_depth" >
                                <tr tal:repeat="(subkeys, subvalues) values.items()">
                                    <th tal:content="subkeys"/>
                                    <td tal:condition="python: not isinstance(subvalues, dict)">
                                        <td tal:content="subvalues[0]"/>
                                        <td tal:content="subvalues[1]"/>
                                    </td>
                                    <td tal:condition="python: isinstance(subvalues, dict)">
                                        <table tal:define="values subvalues"
                                               metal:use-macro="template.macros['filter_depth']"/>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>''')
        matlabheaders = ['Keys', 'Values']
        keydict = MatlabParser(matlabpath).retrieve_structure()
        table_html = table(matlabheaders=matlabheaders, keydictionaries=keydict)
        return Response(table_html)