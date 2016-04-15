import logging
import math
import os
import re

from chameleon import PageTemplate
from pyramid.renderers import render

from finder.requesthandler.directoryRequestHandler import DirectoryRequestHandler
from finder.requesthandler.fileHandler import open_resource


class TemplateHandler:
    def __init__(self):
        pass

    @staticmethod
    def loadCustomTemplate(request, directory_settings, template_src_settings, fallbackoption):
        # TODO: template_str is not used. refactor this or use it
        custom_template_path = None
        base_path = request.registry.settings['root_dir']
        relative_path = DirectoryRequestHandler.requestfolderpath(request)

        if template_src_settings in directory_settings:
            dir_path = directory_settings[template_src_settings]
            possible_prefixes = {'projectlocal:': base_path, 'folderlocal:': relative_path, 'absolute:': ''}

            found = False
            for (prefix, path) in possible_prefixes.items():
                if not dir_path.startswith(prefix):
                    continue
                dir_path = dir_path[len(prefix):]
                custom_template_path = os.path.join(path, dir_path)
                found = True
                break
            if not found:
                log = logging.getLogger(__name__)
                log.info('Specified dir_path starts with unknown prefix: {0}'.format(dir_path))

        # check if the custom_directory_template is valid
        if custom_template_path is not None and not os.path.exists(custom_template_path):
            custom_template_path = None
        if custom_template_path is None:
            custom_template_path = fallbackoption
        return custom_template_path


    @staticmethod
    def _apply_specific_templates(filenames, extension_specific, keypath=None):
        """
        Applies the specific templates which are set in the directory_settings to the list of files
        :param filenames:
        :param extension_specific:
        :return:
        """
        def apply_templates_to_leafnodes(tree, template_leafs):
            def iterate_list(elementlist, template_leafs):
                for i, item in enumerate(elementlist):
                    if isinstance(item, dict):
                        if 'filename' in item:
                            # apply the template on this element
                            try:
                                tmp_html = template_leafs(file=elementlist[i])
                            except BaseException as e:
                                log = logging.getLogger(__name__)
                                log.warning('Error occured while applying custom template {0} {1}', e.message, str(e))
                                tmp_html = 'Error occured while the template was applied to the' \
                                           ' following element: {0} Message: {1}'.format(elementlist[i], e.message)
                            elementlist[i]['html'] = tmp_html
                        else:
                            tree[key][i] = apply_templates_to_leafnodes(elementlist[i], template_leafs)
                    elif isinstance(item, list):
                        elementlist[i] = iterate_list(elementlist[i], template_leafs)
                return elementlist
            if isinstance(tree, dict):
                for (key, value) in tree.items():
                    if isinstance(value, dict) and 'filename' not in value:
                        tree[key] = apply_templates_to_leafnodes(value, template_leafs)
                    elif isinstance(value, list):
                        tree[key] = iterate_list(value, template_leafs)
            elif isinstance(tree, list):
                log = logging.getLogger(__name__)
                log.warning('Element: {0}'.format(tree))
                tree = iterate_list(tree, template_leafs)
            else:
                log = logging.getLogger(__name__)
                log.warning('Got an unexpected type {0}'.format(type(tree)))
            return tree
        if keypath is None:
            keypath = []

        specified_template = extension_specific['template']
        specified_template = 'template/png_template.pt'
        # check if it appears to be a path or an html document
        if re.search('^(?:[a-zA-Z]\:|\\\\[\w\.]+\\[\w.$]+)\\(?:[\w]+\\)*\w([\w.])+$', specified_template):
            print(specified_template)
            # TODO: open load custom template
        else:
            print('didnt match {0}'.format(specified_template))

        # load template and check if it comes from an old version
        template = PageTemplate(extension_specific['template'], keep_body=True)
        if re.search('grouped_files', template.body) is not None:
            log = logging.getLogger(__name__)
            log.warning('Using an old template ==> Not working since update')
            template = PageTemplate('<div>Found an outdated template, while compiling <span tal:content="file"></span></div>'.format(template.body), keep_body=True)
        filedict_with_html = apply_templates_to_leafnodes(filenames, template)

        # compute the column width
        bootstrap_columns = 12
        elements_per_row = extension_specific['elements_per_row']
        column_width = int(math.ceil(bootstrap_columns / elements_per_row))

        # adapting the file path
        if isinstance(filedict_with_html, list):
            filedict_with_html = {keypath[-1]: filedict_with_html}
            keypath = keypath[:-1]

        # "new" step we already applied the template to each individual element and now we format all elements globally
        return render('template/specific_key_template.pt',
                      dict(grouped_files=filedict_with_html, columnwidth=column_width, groups=keypath))

    def apply_templates(self, dict_items, directory_settings, folder_descriptions=None, overwrite_key=None, keypath=[]):
        """
        Apply the template specified in the direcotry settings to all elements in the dict_items dictionary
        """
        logger = logging.getLogger(__name__)
        assert(isinstance(dict_items, dict))
        if not isinstance(directory_settings, dict):
            logger.warning('Directory settings is not a dictionary {0}'.format(type(directory_settings)))
        # apply specific to the items
        for (filter_criteria, filenames) in dict_items.items():
            folder_template = None if 'folder_template' not in directory_settings else directory_settings[
                'folder_template']
            file_template = None if 'file_template' not in directory_settings else directory_settings['file_template']
            special_filetemplates = dict() if 'specific_filetemplates' not in directory_settings else \
            directory_settings['specific_filetemplates']

            if filter_criteria in special_filetemplates:
                tmp_key = keypath + [filter_criteria, ]
                extension_specific = special_filetemplates[filter_criteria]
                html = self._apply_specific_templates(filenames, extension_specific, keypath=tmp_key)
                dict_items[filter_criteria] = [html]
            elif overwrite_key is not None and overwrite_key in special_filetemplates:
                tmp_key = keypath + [filter_criteria, ]
                extension_specific = special_filetemplates[overwrite_key]
                html = self._apply_specific_templates(filenames, extension_specific, keypath=tmp_key)
                dict_items[filter_criteria] = [html]
            else:
                # check for the template
                template = None
                if filter_criteria != '' and not filter_criteria == '..' and file_template is not None:
                    template = PageTemplate(file_template)
                elif filter_criteria == '' and folder_template is not None:
                    template = PageTemplate(folder_template)
                else:
                    logger.warning('Unknown filter_criteria "{0}"'.format(filter_criteria))
                # apply elements to the template
                if template is None:
                    logger.warning('Template is not set: {0}'.format(filter_criteria))
                    if filter_criteria in dict_items:
                        del dict_items[filter_criteria]
                    continue

                tmp = []
                for file in filenames:
                    # preview files
                    tmp.append(template(item=file) if folder_descriptions is None or file not in folder_descriptions else
                               template(item=file, folder_descriptions=folder_descriptions[file]['shortdescription']))
                dict_items[filter_criteria] = tmp
        return dict_items
