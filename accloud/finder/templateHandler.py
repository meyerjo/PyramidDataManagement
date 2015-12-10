import math
from chameleon import PageTemplate


class TemplateHandler:
    def __init__(self):
        pass

    @staticmethod
    def _apply_specific_templates(filenames, extension_specific):
        """
        Applies the specific templates which are set in the directory_settings to the list of files
        :param filenames:
        :param extension_specific:
        :return:
        """
        bootstrap_columns = 12
        elements_per_row = extension_specific['elements_per_row']
        column_width = int(math.ceil(bootstrap_columns / elements_per_row))

        specific_template = PageTemplate(extension_specific['template'])
        html = specific_template(grouped_files=filenames, columnwidth=column_width)
        return html

    def apply_templates(self, dict_items, directory_settings):
        # apply specific to the items
        for (filter_criteria, filenames) in dict_items.items():
            folder_template = None if 'folder_template' not in directory_settings else directory_settings[
                'folder_template']
            file_template = None if 'file_template' not in directory_settings else directory_settings['file_template']
            special_filetemplates = dict() if 'specific_filetemplates' not in directory_settings else \
            directory_settings['specific_filetemplates']

            if filter_criteria in special_filetemplates:
                extension_specific = special_filetemplates[filter_criteria]
                html = self._apply_specific_templates(filenames, extension_specific)
                dict_items[filter_criteria] = [html]
            else:
                template = None
                if filter_criteria != '' and not filter_criteria == '..' and file_template is not None:
                    template = PageTemplate(file_template)
                elif filter_criteria == '' and folder_template is not None:
                    template = PageTemplate(folder_template)
                if template is not None:
                    tmp = [template(item=file) for file in filenames]
                    dict_items[filter_criteria] = tmp
        return dict_items
