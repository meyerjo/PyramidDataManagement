import h5py
import jsonpickle
import math
import numpy as np


class MatlabParser:
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
        dataset = np.transpose(data)
        return dataset

    def _traverse_h5pygroups(self, fileref, group):
        if len(group) > self._groupmaximum and isinstance(group, h5py.Group):
            return str(group)
        if not isinstance(group, h5py.Group):
            return self._parse_dataset(fileref, group)
        output = dict(zip(group.keys(), [None] * len(group.keys())))
        for key in group.keys():
            if len(group[key]) <= self._groupmaximum:
                output[key] = self._traverse_h5pygroups(fileref, group[key])
            else:
                output[key] = str(group[key])
        return output

    def _parse_dataset(self, fileref, dataset):
        shape = dataset.shape
        prod = 1
        for i in range(0, len(shape)):
            prod *= shape[i]
        if prod > self._datasetmaximum:
            return shape, str(dataset)
        if str(dataset.dtype) in self._fileParserFcn:
            dataset = self._fileParserFcn[str(dataset.dtype)](fileref, dataset)
        else:
            dataset = 'Unparsed: {0}\t{1}\tDatatype unknown:{2}'.format(str(dataset.dtype), str(dataset),
                                                                        str(dataset.dtype))
        return shape, dataset

    def retrieve_structure(self):
        with h5py.File(self._filename) as matfile:
            matlabkeys = matfile.keys()
            emptyvalues = [None] * len(matlabkeys)
            keydict = dict(zip(matlabkeys, emptyvalues))

            for key in keydict.keys():
                currentkey = matfile[key]
                keydict[key] = self._traverse_h5pygroups(matfile, currentkey)
        return keydict

    def specific_element(self, keypath):
        with h5py.File(self._filename) as matfile:
            tmp = matfile
            for key in keypath:
                if key in tmp.keys():
                    tmp = tmp[key]
            if isinstance(tmp, h5py.Dataset):
                self._datasetmaximum = float('inf')
                return tmp.shape, self._parse_dataset(matfile, tmp)
            elif isinstance(tmp, h5py.Group):
                print('Found group' + str(tmp))
            else:
                print('Nothing')