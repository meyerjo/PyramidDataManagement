import logging

import h5py
import numpy as np
import re


class MatlabParser:
    # TODO: this only works for files saved in the -v7.3 format ==> make it more general
    def __init__(self, filename, datasetmaximum=200, groupmaximum=200):
        self._filename = filename
        self._groupmaximum = groupmaximum
        self._datasetmaximum = datasetmaximum
        self._fileParserFcn = {'float64': self._parser_float64,
                               'uint64': self._parser_float64,
                               'uint16': self._parser_uint16,
                               'uint8': self._parser_uint8,
                               'object': self._parser_object}

    @staticmethod
    def _parser_float64(fileref, dataset):
        dataset = np.float64(dataset)
        if dataset.shape == (1, 1):
            dataset = dataset[0][0]
        return dataset

    @staticmethod
    def _parser_uint16(fileref, dataset):
        try:
            return u''.join(unichr(c) for c in dataset)
        except BaseException as e:
            return 'Unparsed: {0}\t{1}\tException occured:{2}'.format(str(dataset.dtype), str(dataset), str(e))

    @staticmethod
    def _parser_uint8(fileref, dataset):
        try:
            if dataset.shape == (1, 1):
                return str(dataset[0][0])
            else:
                return u''.join(unichr(c) for c in dataset)
        except BaseException as e:
            return 'Unparsed: {0}\t{1}\tException occured:{2}'.format(str(dataset.dtype), str(dataset), str(e))

    @staticmethod
    def _parser_object(fileref, dataset):
        data = []
        try:
            for column in dataset:
                row_data = []
                for row_number in range(len(column)):
                    row_data.append(''.join(map(unichr, fileref[column[row_number]][:])))
                data.append(row_data)
        except BaseException as e:
            print('\t' + str(dataset.dtype))
            print('\t' + str(type(dataset)))
            print('\t' + str(e))
            return 'Parsing failed'
        dataset = np.transpose(data)
        return dataset

    def _traverse_h5pygroups(self, fileref, group, keypath, groupmaximum=None, datasetmaximum=None):
        """
        Traverses the "tree-structure" of a matlab file
        :param fileref:
        :param group:
        :param keypath:
        :param groupmaximum:
        :param datasetmaximum:
        :return:
        """
        if groupmaximum is None:
            groupmaximum = self._groupmaximum
        if datasetmaximum is None:
            datasetmaximum = self._datasetmaximum

        if len(group) > groupmaximum and isinstance(group, h5py.Group):
            id = '&'.join(keypath)
            return (len(group), 1), str(group), False, id

        if not isinstance(group, h5py.Group):
            id = '&'.join(keypath)
            return self._parse_dataset(fileref, group, datasetmaximum) + (id,)

        output = dict(zip(group.keys(), [None] * len(group.keys())))
        for key in group.keys():
            if len(group[key]) <= groupmaximum:
                output[key] = self._traverse_h5pygroups(fileref, group[key], keypath + [key], groupmaximum,
                                                        datasetmaximum)
            else:
                output[key] = str(group[key])
        return output

    def _parse_dataset(self, fileref, dataset, datasetmaximum=None):
        """
        Outputs information about the dataset in a matlab file
        :param fileref:
        :param dataset:
        :param datasetmaximum:
        :return:
        """
        if datasetmaximum is None:
            datasetmaximum = self._datasetmaximum
        shape = dataset.shape
        prod = np.prod(np.array(shape))
        if prod > datasetmaximum:
            return shape, str(dataset), False
        if str(dataset.dtype) in self._fileParserFcn:
            dataset = self._fileParserFcn[str(dataset.dtype)](fileref, dataset)
        else:
            dataset = 'Unparsed: {0}\t{1}\tDatatype unknown:{2}'.format(str(dataset.dtype), str(dataset),
                                                                        str(dataset.dtype))
        return shape, dataset, True

    def retrieve_structure(self):
        """
        Outputs the file structure from the matlab file
        :return:
        """
        try:
            with h5py.File(self._filename) as matfile:
                matlabkeys = matfile.keys()
                emptyvalues = [None] * len(matlabkeys)
                keydict = dict(zip(matlabkeys, emptyvalues))

                for key in keydict.keys():
                    currentkey = matfile[key]
                    keypath = [key]
                    keydict[key] = self._traverse_h5pygroups(matfile, currentkey, keypath)
        except BaseException as e:
            log = logging.getLogger(__name__)
            log.error(e.message)
            keydict = dict(error='Error: {0}b'.format(str(e)))

        return keydict

    def specific_element(self, keypath):
        """
        Queries a specific key path in order to reload content
        :param keypath:
        :return:
        """
        with h5py.File(self._filename) as matfile:
            tmp = matfile
            for key in keypath:
                if key in tmp.keys():
                    tmp = tmp[key]
            if isinstance(tmp, h5py.Dataset):
                return self._parse_dataset(matfile, tmp, float('inf')) + ('&'.join(keypath),)
            elif isinstance(tmp, h5py.Group):
                return self._traverse_h5pygroups(matfile, tmp, [], float('inf')) + ('&'.join(keypath),)
            else:
                return None, None

    def compare_multiple_files(self, filenames):
        """
        Compares multiple mat files and outputs the common fieldnames, contained
        in all files
        :param filenames:
        :return:
        """
        keys = None
        for filename in filenames:
            if re.search('\.mat$', filename) is None:
                continue
            with h5py.File(filename) as matfile:
                if keys is None:
                    keys = matfile.keys()
                else:
                    keys = list(set(keys).intersection(matfile.keys()))
        return keys
