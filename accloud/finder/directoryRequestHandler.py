import os


class DirectoryRequestHandler:

    @staticmethod
    def requestfolderpath(request):
        return os.path.join(
            request.registry.settings['root_dir'],
            request.matchdict['dir'])

    @staticmethod
    def requestfilepath(request):
        return os.path.join(
            request.registry.settings['root_dir'],
            request.matchdict['file'])

    @staticmethod
    def handle_request(request, relative_path, directory_settings):
        pass
