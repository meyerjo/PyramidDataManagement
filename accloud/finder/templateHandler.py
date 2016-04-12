import logging
import math
import os

from chameleon import PageTemplate
from pyramid.renderers import render

from finder.requesthandler.directoryRequestHandler import DirectoryRequestHandler


class TemplateHandler:
    def __init__(self):
        pass

    @staticmethod
    def loadCustomTemplate(request, directory_settings, template_str, fallbackoption):
        # TODO: template_str is not used. refactor this or use it
        custom_template_path = None
        base_path = request.registry.settings['root_dir']
        relative_path = DirectoryRequestHandler.requestfolderpath(request)

        if 'directory_template_path' in directory_settings:
            dir_path = directory_settings['directory_template_path']
            if dir_path.startswith('projectlocal:'):
                dir_path = dir_path[len('projectlocal:'):]
                custom_template_path = os.path.join(base_path, dir_path)
            elif dir_path.startswith('folderlocal:'):
                dir_path = dir_path[len('folderlocal:')]
                custom_template_path = os.path.join(relative_path, dir_path)
            elif dir_path.startswith('absolute:'):
                dir_path = dir_path[len('absolute:'):]
                custom_template_path = dir_path

        # check if the custom_directory_template is valid
        if custom_template_path is not None and not os.path.exists(custom_template_path):
            custom_template_path = None
        if custom_template_path is None:
            custom_template_path = fallbackoption
        return custom_template_path


    @staticmethod
    def _apply_specific_templates(filenames, extension_specific, keypath=[]):
        """
        Applies the specific templates which are set in the directory_settings to the list of files
        :param filenames:
        :param extension_specific:
        :return:
        """
        def iterate_structure(tree, template_leafs):
            def iterate_list(elementlist, template_leafs):
                for i, item in enumerate(elementlist):
                    if isinstance(item, dict):
                        if 'filename' in item:
                            # apply the template on this element
                            tmp_html = template_leafs(file=elementlist[i])
                            elementlist[i]['html'] = tmp_html
                        else:
                            tree[key][i] = iterate_structure(elementlist[i], template_leafs)
                    elif isinstance(item, list):
                        elementlist[i] = iterate_list(elementlist[i], template_leafs)
                return elementlist
            if isinstance(tree, dict):
                for (key, value) in tree.items():
                    if isinstance(value, dict) and 'filename' not in value:
                        tree[key] = iterate_structure(value, template_leafs)
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

        template_leafs = '''
        <tal:block tal:switch="'filename' in file">
            <div class='row-fluid' tal:case='True'>
                <tal:block tal:switch="python: ('label' in file) and (isinstance(file, dict))">
                    <tal:block tal:case="True">
                        <div class='col-sm-12'>
                            Label: <span tal:content="file.label"></span>
                        </div>
                    </tal:block>
                    <tal:block tal:case="False">
                        <div class='col-sm-12'>
                            File: <span tal:content="file.filename"></span>
                        </div>
                    </tal:block>
                </tal:block>
                <div class='col-sm-12'>
                    <a tal:attributes='href file.filename; data-title file.filename' data-toggle='lightbox'>
                        <img tal:attributes="src file.filename" class='col-sm-12'>
                    </a>
                </div>
            </div>
            <div class="row-fluid" tal:case="False">
                Field missing ${file}
            </div>
        </tal:block>
        '''
        test = PageTemplate(template_leafs)
        filedict_with_html = iterate_structure(filenames, test)

        bootstrap_columns = 12
        elements_per_row = extension_specific['elements_per_row']
        column_width = int(math.ceil(bootstrap_columns / elements_per_row))

        #specific_template = PageTemplate(extension_specific['template'])
        #html = specific_template(grouped_files=filenames, columnwidth=column_width, labels=element_labels)
        if isinstance(filedict_with_html, list):
            # TODO: check if there is a better solution
            filedict_with_html = {keypath[-1]: filedict_with_html}
            keypath = keypath[:-1]

        html = render('template/specific_key_template.pt',
                      dict(grouped_files=filedict_with_html, columnwidth=column_width, groups=keypath))
        return html

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
                if template is not None:
                    tmp = []
                    print(filenames)
                    for file in filenames:
                        # preview files
                        print(file)
                        if folder_descriptions is not None and file in folder_descriptions:
                            tmp.append(template(item=file, folderdescription=folder_descriptions[file]['shortdescription']))
                        else:
                            tmp.append(template(item=file))
                    dict_items[filter_criteria] = tmp
                else:
                    logger.warning('Template is not set: {0}'.format(filter_criteria))
                    if filter_criteria in dict_items:
                        del dict_items[filter_criteria]
        return dict_items
