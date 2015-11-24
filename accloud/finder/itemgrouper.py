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
                    matrix[i, j] = sys.maxint - 1
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
        groups = []
        tmp_group = []
        for item in sorted(items):
            tmp_row.append(item)
            if len(tmp_group) == elements_per_group:
                groups.append(tmp_row)
                tmp_row = []
        if tmp_row is not []:
            groups.append(tmp_row)
        return groups

    def group(self, items, elements_per_group, method='alphabetical'):
        if method == 'alphabetical':
            return self._alphabetical_grouping(items, elements_per_group)
        elif method == 'numerical':
            matrix = self._compute_edit_distance_matrix(items)
            groups = self._group_by_matrix(items, matrix, elements_per_group)
            return groups
        else:
            return items
