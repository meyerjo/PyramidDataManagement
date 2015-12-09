import HTMLParser
import os
import shutil

import jsonpickle
from pyramid.renderers import render
from pyramid.response import Response

from accloud.finder.directoryRequestHandler import DirectoryRequestHandler


class DirectoryCreateLocalSettings(DirectoryRequestHandler):
    @staticmethod
    def handle_request(request, relative_path, directory_settings):
        """
        Creates the local settings file for the corresponding directory
        :param request:
        :param directory_settings:
        :return:
        """
        try:
            with open(relative_path + '/.settings.json', 'w') as settings_file:
                settings_file.write(jsonpickle.encode(directory_settings, unpicklable=False))
            return None
        except IOError as e:
            return e.message


class DirectoryUpdateLocalSettings(DirectoryRequestHandler):
    @staticmethod
    def handle_request(request, relative_path, directory_settings):
        params_json = dict(request.params)
        newsettingstring = params_json['newsettings']
        newsettingstring = HTMLParser.HTMLParser().unescape(newsettingstring)
        try:
            newsettingsobj = jsonpickle.decode(newsettingstring)
            shutil.copyfile(relative_path, relative_path + '_bak')
            with open(relative_path, 'w') as file:
                file.write(newsettingsobj)
        except Exception as e:
            return Response(render('json', {'error': e.message}))
        return Response(render('json', {'error': None}))


class DirectoryLoadSettings(DirectoryRequestHandler):
    @staticmethod
    def handle_request(request, relative_path, directory_settings):
        """
        Load the directory settings for the specific directory. Checks if it is indicated that a reload is required.
        :param directorypath: Path of the folder, which should load the files
        :param directorysettings: Dictionary with the specific directory settings
        :return:
        """
        basepath = request.registry.settings['root_dir']

        if relative_path in directory_settings:
            localsettings = directory_settings[relative_path]
            if 'reload' in localsettings:
                reload_templates = localsettings['reload']
                if reload_templates:
                    if os.path.exists(localsettings['path']):
                        with open(localsettings['path'], "r") as myfile:
                            data = myfile.read()
                            localsettings = jsonpickle.decode(data)
                            return localsettings
                return localsettings
            return localsettings
        else:
            # check if the parent folder has some marked settings
            previous_folder = os.path.abspath(relative_path + '/../')
            previous_folder = previous_folder.encode('string-escape')
            previous_folder = previous_folder.decode('string-escape')
            if relative_path == basepath:
                return dict()

            return DirectoryLoadSettings.handle_request(request, previous_folder, directory_settings)