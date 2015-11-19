import csv
import os
from contextlib import contextmanager
import hoedown
from chameleon import PageTemplate
from pyramid.exceptions import NotFound
from pyramid.renderers import render
from pyramid.response import Response
from pyramid.view import view_config


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

    @view_config(route_name='csv', renderer='template/index.pt')
    def csv_table(self):
        # TODO: delimiter choice
        relative_path = os.path.join(
            self.request.registry.settings['root_dir'],
            self.request.matchdict['file'])

        with self.open_resource(relative_path) as csv_file:
            reader = csv.reader(csv_file)
            table = PageTemplate('''<table class="table table-striped table-bordered table-condensed">
                <tr tal:repeat="row table"><td tal:repeat="cell row" tal:content="cell"/></tr>
                </table>''')
            table_html = table(table=reader)
            return {"request": self.request, "html": table_html, "files": dict(), "folders": ['.', '..']}

    @view_config(route_name='markdown', renderer='template/markdown.pt')
    def markdown(self):
        markdown_path = os.path.join(
            self.request.registry.settings['root_dir'],
            self.request.matchdict['file'])
        with self.open_resource(markdown_path) as markdown_file:
            source = markdown_file.read()
            html = hoedown.Markdown(
                hoedown.HtmlRenderer(hoedown.HTML_TOC_TREE),
                hoedown.EXT_TABLES).render(source)
            return {"request": self.request, "html": html, "files": dict(), "folders": ['.', '..']}

    @view_config(route_name='matlab', renderer='template/index.pt')
    def matlab(self):
        matlab_path = os.path.join(
            self.request.registry.settings['root_dir'],
            self.request.matchdict['file'])

        with self.open_resource(matlab_path) as matlab_file:
            source = matlab_file.read()
            matlab_html = render('template/matlab.pt', {"request": self.request, "html": source})
            return {"request": self.request, "html": matlab_html, "files": dict(), "folders": ['.', '..']}
