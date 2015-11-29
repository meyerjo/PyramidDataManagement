import logging
import mimetypes
import os
import re

from accloud.finder.itemgrouper import ItemGrouper


class MarkdownExport:
    def __init__(self, request):
        self._request = request
        self._log = logging.getLogger(__name__)

    def _markdown_table(self, items):
        assert (isinstance(items, list))
        output = '|'
        for item in items:
            output += '{0}|'.format(item)
        output += '\n|'
        for item in items:
            output += '---|'
        output += '\n|'
        for item in items:
            output += '![]({0})|'.format(item)
        output += '\n'
        return output

    def _iterate_folder(self, menustring, items):
        if isinstance(items, list):
            output = ''
            for item in items:
                if isinstance(item, list):
                    # implement specific behaviour for some files
                    firstitem = item[0]
                    if isinstance(firstitem, unicode) or isinstance(firstitem, str):
                        filemime = mimetypes.guess_type(firstitem)
                        if re.match('^image', filemime[0]):
                            output += self._markdown_table(item)
                        else:
                            output += self._iterate_folder('#' + menustring, item)
                    else:
                        output += self._iterate_folder('#' + menustring, item)
                else:
                    output += '{0} {1}\n'.format('*', item)
            output += '\n'
            return output
        elif isinstance(items, dict):
            output = ''
            for (key, values) in sorted(items.items()):
                output += '{0} {1}\n'.format(menustring, key)
                output += self._iterate_folder('#' + menustring, values)
            return output
        else:
            self._log.warning('Something went wrong. The type {0} is unexpected'.format(str(type(items))))
            return ''

    def export_folder(self, folder, directory_settings=None, filter=None):
        # get the directory content
        # relative_path = os.path.join(
        #     self._request.registry.settings['root_dir'],
        #     self._request.matchdict['dir'])
        relative_path = folder
        listing = os.listdir(relative_path)
        relative_path = str(os.path.abspath(relative_path)).encode('string-escape')
        relative_path = relative_path.decode('string-escape')

        # filter the folder content
        itemgrouper = ItemGrouper()
        visible_items_by_extension = itemgrouper.group_folder(listing, directory_settings)

        # filter the specific file extension
        if filter is not None:
            if filter in visible_items_by_extension:
                visible_items_by_extension = visible_items_by_extension[filter]

        # iterate through the file
        output = self._iterate_folder('#', visible_items_by_extension)
        return output


class PresentationMarkdownExport(MarkdownExport):
    def __init__(self, request):
        MarkdownExport.__init__(self, request)

    def _iterate_folder(self, menustring, items):
        if isinstance(items, list):
            output = ''
            for item in items:
                if isinstance(item, list):
                    # implement specific behaviour for some files
                    firstitem = item[0]
                    if isinstance(firstitem, unicode) or isinstance(firstitem, str):
                        filemime = mimetypes.guess_type(firstitem)
                        if re.match('^image', filemime[0]):
                            output += self._markdown_table(item)
                            continue
                    output += self._iterate_folder('#' + menustring, item)
                elif isinstance(item, unicode) or isinstance(item, str):
                    output += '{0} {1}\n'.format('*', item)
                else:
                    self._log.warning('The type is unknown {0}'.format(str(type(item))))
            output += '\n'
            return output
        elif isinstance(items, dict):
            output = ''
            for (key, values) in sorted(items.items()):
                output += '{0} {1}\n'.format(menustring, key)
                if len(menustring) == 1 and isinstance(values, dict):
                    output += '---\n'
                output += self._iterate_folder('#' + menustring, values)
                output += '---\n\n'
            return output
        else:
            self._log.warning('Something went wrong. The type {0} is unexpected'.format(str(type(items))))
            return ''

    def _markdown_table(self, items):
        assert (isinstance(items, list))
        output = '|'
        for item in items:
            n = 30
            splititem = [item[i:i + n] for i in range(0, len(item), n)]
            output += '{0}|'.format('<br/>'.join(splititem))
        output += '\n|'
        for item in items:
            output += '---|'
        output += '\n|'
        for item in items:
            output += '<img src="{0}" width="100%"/>|'.format(item)
        output += '\n'
        return output
