import os
import tempfile
from zipfile import ZipFile

from pyramid.response import Response

from accloud.finder.directoryRequestHandler import DirectoryRequestHandler
from accloud.finder.itemgrouper import ItemGrouper


class DirectoryZipHandler(DirectoryRequestHandler):

    @staticmethod
    def _file_tuples(depth, keypath, item):
        coll = []
        if isinstance(item, dict):
            for (key, values) in item.items():
                if keypath != '':
                    keypath += '/'
                newkeypath = keypath + key
                if depth < 1:
                    newkeypath = ''
                coll = coll + DirectoryZipHandler._file_tuples(depth + 1, newkeypath, values)
            return coll
        elif isinstance(item, list):
            for it in item:
                coll = coll + DirectoryZipHandler._file_tuples(depth, keypath, it)
            return coll
        else:
            return [(item, keypath + '/' + item,)]

    @staticmethod
    def handle_request(request, relative_path, directory_settings):
        depth = 0
        listing = os.listdir(relative_path)
        relative_path = str(os.path.abspath(relative_path)).encode('string-escape')
        relative_path = relative_path.decode('string-escape')

        returnfilename = os.path.basename(relative_path)

        # filter the folder content
        itemgrouper = ItemGrouper()
        items_dict, visibleitems, invisibleitems = itemgrouper.group_folder(listing, directory_settings)

        if 'specific' in dict(request.params):
            specific_filetype = request.params['specific']
            if specific_filetype in items_dict:
                items_dict = items_dict[specific_filetype]
                returnfilename += '_' + specific_filetype
                depth = 1

        # TODO: Sometimes zip file creation doesnt halt. It seems to be dependent on the fact whether another request.zip file already exists
        nosubfolderallowed = 'key_not_as_folder_separator' in dict(request.params)
        tuples = DirectoryZipHandler._file_tuples(depth, '', items_dict)
        tempdirpath = tempfile.mkdtemp()
        zippath = tempdirpath + '/request.zip'
        with ZipFile(zippath, 'w') as zip:
            for tuple in tuples:
                localfilepath = relative_path + '/' + tuple[0]
                if tuple[0].startswith('.'):
                    continue
                if os.path.isdir(localfilepath):
                    continue
                if nosubfolderallowed:
                    zip.write(localfilepath, tuple[0])
                else:
                    zip.write(localfilepath, tuple[1])
        with open(zippath, 'rb') as zip:
            return Response(body=zip.read(),
                            content_type='application/zip',
                            content_disposition='attachment; filename="{0}.zip"'.format(returnfilename))
