from contextlib import contextmanager

from pyramid.exceptions import NotFound


@contextmanager
def open_resource(filename, mode="r"):
    try:
        print(filename)
        f = open(filename, mode)
    except IOError:
        raise NotFound
    else:
        try:
            yield f
        finally:
            f.close()