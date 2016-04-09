import logging
import mimetypes
import os
import re

from finder.requesthandler.itemgrouper import ItemGrouper


class MarkdownExport:
    def __init__(self, request):
        self._request = request
        self._log = logging.getLogger(__name__)
        self._folder = None

    def _markdown_table(self, items):
        assert (isinstance(items, list))
        output = '|'
        for item in items:
            output += '{0}|'.format(item)
        output += '\n|'
        for q in range(0, len(items)):
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
        self._folder = folder
        relative_path = folder
        listing = os.listdir(relative_path)
        relative_path = str(os.path.abspath(relative_path)).encode('string-escape')
        relative_path = relative_path.decode('string-escape')

        # filter the folder content
        itemgrouper = ItemGrouper()
        visible_items_by_extension, visibleitems, invisibleitems = itemgrouper.group_folder(listing, directory_settings)

        # filter the specific file extension
        if filter is not None:
            if filter in visible_items_by_extension:
                visible_items_by_extension = visible_items_by_extension[filter]

        output = ''
        if os.path.exists(relative_path + '/.intro.md'):
            with open(relative_path + '/.intro.md') as file:
                output += file.read()
        # iterate through the file
        output += self._iterate_folder('#', visible_items_by_extension)
        if os.path.exists(relative_path + '/.outro.md'):
            with open(relative_path + '/.outro.md') as file:
                output += file.read()
        return output


class PresentationMarkdownExport(MarkdownExport):
    def __init__(self, request):
        MarkdownExport.__init__(self, request)

    def _load_key_specific_comment(self, key):
        output = ''
        keyspecificcommentfile = self._folder + '/.{0}.md'.format(key)
        if os.path.exists(keyspecificcommentfile):
            with open(keyspecificcommentfile) as commentfile:
                output += commentfile.read()
                output += '\n---\n\n'
        elif os.path.exists(self._folder + '/.notes.md'):
            # TODO: put this into one regular expression and make it possible to specify this regex externally
            with open(self._folder + '/.notes.md') as file:
                filecontent = file.read()
                regex = re.compile('#\s{0}'.format(key), re.MULTILINE)
                m = regex.search(filecontent)
                if m is not None:
                    filespecific_content = filecontent[m.start():]
                    next_vp = re.search('#\sVP[0-9]{2}', filespecific_content[m.end()-m.start():])
                    if next_vp is not None:
                        filespecific_content = filespecific_content[:next_vp.end()]
                    output += filespecific_content
                    if re.search('---', filespecific_content[-6:]) is None:
                        output += '---\n'
        return output

    def _iterate_folder(self, menustring, items, lastkey = ''):
        if isinstance(items, list):
            output = ''
            expected_items = None
            for i, item in enumerate(items):
                if isinstance(item, list):
                    # TODO: make this recursive becaus so far, it only can handle a fixed depth of array(array(elements))
                    expected_items = max(expected_items, len(item))
                    # implement specific behaviour for some files
                    if len(item) == 0:
                        continue
                    firstitem = item[0]
                    if isinstance(firstitem, unicode) or isinstance(firstitem, str):
                        # implement specific behaviour for some files
                        filemime = mimetypes.guess_type(firstitem)
                        if re.match('^image', filemime[0]):
                            output += self._markdown_table(item, expected_items)
                            if i + 1 < len(items):
                                output += '---\n\n'
                                output += '{0} {1}\n'.format(menustring[1:], lastkey)
                            continue
                    output += self._iterate_folder('#' + menustring, item, lastkey)
                elif isinstance(item, unicode) or isinstance(item, str):
                    output += '{0} {1}\n'.format('*', item, lastkey)
                else:
                    print('The type is unknown {0}'.format(str(type(item))))
            output += '\n'
            return output
        elif isinstance(items, dict):
            output = ''
            for (key, values) in sorted(items.items()):
                output += self._load_key_specific_comment(key)
                output += '{0} {1}\n'.format(menustring, key)
                if len(menustring) == 1 and isinstance(values, dict):
                    output += '---\n'
                output += self._iterate_folder('#' + menustring, values, key)
                output += '---\n\n'
            return output
        else:
            print('Something went wrong. The type {0} is unexpected. {1}'.format(str(type(items)), str(items)))
            return ''

    def _markdown_table(self, items, expected_items):
        assert (isinstance(items, list))
        expected_items = max(2, expected_items)
        output = '|'
        for item in items:
            item = str(item)
            # TODO: move this to an external part
            item = os.path.splitext(item)[0]
            item = item[5:]
            n = 50
            splititem = [item[i:i + n] for i in range(0, len(item), n)]
            output += '{0}|'.format('<br/>'.join(splititem))
        if len(items) < expected_items:
            for i in range(0, expected_items - len(items)):
                output += '|'
        output += '\n|'

        for item in range(expected_items):
            output += '---|'

        output += '\n|'
        for item in items:
            imagewidthhack = int((len(items) / float(expected_items)) * 100)
            output += '<img src="{0}" width="{1}%"/>|'.format(item, imagewidthhack)
        if len(items) < expected_items:
            for i in range(0, expected_items - len(items)):
                output += '|'
        output += '\n\n'
        return output
