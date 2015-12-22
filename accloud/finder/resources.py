from pyramid.security import Allow, Everyone, Authenticated


class Root(object):
    __name__ = None
    __acl__ = [(Allow, Authenticated, 'view'),
               (Allow, 'group:editors', 'edit')]

    def __init__(self, request):
        pass