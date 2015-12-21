from contextlib import contextmanager

from werkzeug.exceptions import NotFound


class CSVHandler:

    @contextmanager
    def open_resource(self, filename, mode="r"):
        try:
            f = open(filename, mode)
        except IOError:
            raise NotFound
        else:
            try:
                yield f
            finally:
                f.close()

    @staticmethod
    def _detect_csv_delimiter(text, possible_delimiter=None):
        if not possible_delimiter:
            possible_delimiter = ['\t', ',', ';', ' ']
        min_delimiter = 0
        delimit = possible_delimiter[0]
        for delimiter in possible_delimiter:
            count = text.count(delimiter)
            if count > min_delimiter:
                delimit = delimiter
                min_delimiter = count
        return delimit

    @staticmethod
    def getdelimiter(path, requestdictionary):
        auto_detect_delimiter = False
        if 'delimiter' in requestdictionary:
            delimit = str(requestdictionary['delimiter'])
            if delimit in ['tab', '/t']:
                delimit = str('\t')
            elif delimit == 'space':
                delimit = str(' ')
            elif delimit == 'auto':
                auto_detect_delimiter = True
                delimit = str(',')
        else:
            auto_detect_delimiter = True
            delimit = str(',')

        if auto_detect_delimiter:
            with path.open_resource(path) as csv_file:
                possible_delimiters = ['\t', ',', ';', ' ']
                delimit = path._detect_csv_delimiter(csv_file.read(), possible_delimiters)
        return delimit