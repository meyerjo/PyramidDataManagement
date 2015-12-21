import os
import time

from markdown import markdown
from pdfkit import pdfkit
from pyramid.renderers import render
from pyramid.response import Response

from accloud.finder.directoryRequestHandler import DirectoryRequestHandler
from accloud.finder.markdownexport import PresentationMarkdownExport, MarkdownExport


class PresentationExportHandler(DirectoryRequestHandler):
    @staticmethod
    def handle_request(request, relative_path, directory_settings):
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


class ReportExportHandler(DirectoryRequestHandler):
    @staticmethod
    def handle_request(request, relative_path, directory_settings):
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
