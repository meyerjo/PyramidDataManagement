import os
import re

import numpy
import sys
from Levenshtein._levenshtein import distance


class ItemGrouper:
    def __init__(self):
        pass

    def _compute_edit_distance_matrix(self, input):
        """
        Computes the edit distance between the
        :param input:
        :return:
        """
        matrix = numpy.zeros(shape=(len(input), len(input)))
        for i, item_a in enumerate(input):
            for j, item_b in enumerate(input):
                if i == j:
                    matrix[i, j] = sys.maxint - 1000
                else:
                    matrix[i, j] = distance(item_a, item_b)
        return matrix

    def _group_by_matrix(self, input, matrix, items_per_row):
        """
        Groups the elements in input into rows using the weights contained in matrix.
        :param input:
        :param matrix:
        :param items_per_row:
        :return:
        """
        rows = []
        tmp_row = []
        minvalue = matrix.min()
        elements_to_add = len(input)
        # TODO: refactor this, should be more pretty
        while minvalue != sys.maxint:
            index = numpy.unravel_index(matrix.argmin(), matrix.shape)
            elements = [input[index[0]], input[index[1]]]

            for element in elements:
                tmp_row.append(element)
                elements_to_add -= 1
                if len(tmp_row) == items_per_row:
                    rows.append(tmp_row)
                    tmp_row = []
                if elements_to_add == 0 and len(tmp_row) > 0:
                    rows.append(tmp_row)
                    tmp_row = []

            # prevent this tuple from further existing
            matrix[index] = sys.maxint
            matrix[index[1], index[0]] = sys.maxint

            # if the row is full then we can eliminate the files, otherwise we have to leave space for 
            if len(tmp_row) == 0:
                matrix[index[0], :] = sys.maxint
                matrix[index[1], :] = sys.maxint
                matrix[:, index[0]] = sys.maxint
                matrix[:, index[1]] = sys.maxint
            minvalue = matrix.min()
        return rows

    def _alphabetical_grouping(self, items, elements_per_group):
        """
        Groups the items alphabetically into rows
        :param items:
        :param elements_per_group:
        :return:
        """
        groups = []
        tmp_group = []
        for item in sorted(items):
            tmp_group.append(item)
            if len(tmp_group) == elements_per_group:
                groups.append(tmp_group)
                tmp_group = []
        if tmp_group is not []:
            groups.append(tmp_group)
        return groups

    def _reorganize_files_by_extension(self, files, blacklist=None):
        if not blacklist:
            blacklist = []
        visible_items_by_extension = dict()
        visible_items = []
        invisible_items = []
        for item in files:
            filename, file_extension = os.path.splitext(item)
            if not item.startswith('.'):
                skipfile = False
                for rule in blacklist:
                    if rule == '':
                        continue
                    if re.search(rule, item) is not None:
                        skipfile = True
                        break
                if skipfile:
                    continue
                visible_items.append(item)
                if file_extension in visible_items_by_extension:
                    visible_items_by_extension[file_extension].append(item)
                else:
                    visible_items_by_extension[file_extension] = [item]
            else:
                invisible_items.append(item)
        return visible_items_by_extension, visible_items, invisible_items

    def _apply_filter_to_items(self, items, filter):
        """
        Gets a list of string items and a list of filtercriteria consisting of regular_expressions and filters them into a dictionary
        :param items: list of strings
        :param filter: list of regular expressions
        :return: filtered dictionary
        """
        assert (isinstance(filter, str) or isinstance(filter, unicode))
        returning_dict = dict()
        for item in items:
            match = re.search(filter, item)
            if match is None:
                print('Couldn\'t group the following item, because the regex failed {0} {1}'.format(item, filter))
                continue
            if match.group() in returning_dict:
                returning_dict[match.group()].append(item)
            else:
                returning_dict[match.group()] = [item]
        return returning_dict

    def _filter_to_dict(self, items, filtercriteria):
        assert (len(filtercriteria) >= 1)
        returning_dict = dict()
        if isinstance(items, list):
            returning_dict = self._apply_filter_to_items(items, str(filtercriteria[0]))
        if len(filtercriteria) == 1:
            return returning_dict

        for (key, values) in returning_dict.items():
            returning_dict[key] = self._filter_to_dict(values, filtercriteria[1:])
        return returning_dict

    def _split_files_into_subgroups(self, input, items_per_row, grouping_method='numerical'):
        assert (items_per_row >= 1)
        if isinstance(input, list):
            return self.group(input, items_per_row, grouping_method)
        elif isinstance(input, dict):
            for (key, value) in input.items():
                input[key] = self._split_files_into_subgroups(value, items_per_row)
            return input
        else:
            print('Something went wrong. The type of the input isn\'t a dict '
                  'or a list. {0}'.format(str(type(input))))
            return input

    def _group_files_by_specific_criteria(self, files, extension_specific):
        errors = []
        try:
            grouped_files = self._filter_to_dict(files, extension_specific['group_by'])
        except Exception as e:
            grouped_files = []
            errors.append(e.message)
        elements_per_row = extension_specific['elements_per_row']
        row_group_files = self._split_files_into_subgroups(grouped_files, elements_per_row)
        return row_group_files, errors

    def group(self, items, elements_per_group, method='numerical'):
        if method == 'alphabetical':
            return self._alphabetical_grouping(items, elements_per_group)
        elif method == 'numerical':
            matrix = self._compute_edit_distance_matrix(items)
            groups = self._group_by_matrix(items, matrix, elements_per_group)
            return groups
        else:
            return items

    def group_folder(self, files, directory_settings):
        # restructure files and split them according to their fileextension
        if 'blacklist' in directory_settings:
            visible_items_by_extension, visible_items, invisible_items = \
                self._reorganize_files_by_extension(files, directory_settings['blacklist'])
        else:
            visible_items_by_extension, visible_items, invisible_items = \
                self._reorganize_files_by_extension(files)
        visible_items_by_extension['..'] = ['..']

        # filter files
        for (extension, filenames) in visible_items_by_extension.items():
            if 'specific_filetemplates' in directory_settings:
                if extension in directory_settings['specific_filetemplates']:
                    extension_specific = directory_settings['specific_filetemplates'][extension]
                    groupedfiles, errors = self._group_files_by_specific_criteria(filenames, extension_specific)
                    visible_items_by_extension[extension] = groupedfiles

        return visible_items_by_extension, visible_items, invisible_items
