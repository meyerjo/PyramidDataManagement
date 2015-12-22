from pyramid.security import Allow, Everyone, Authenticated, ALL_PERMISSIONS


class Root(object):
    __name__ = None
    __acl__ = [(Allow, Authenticated, 'authenticatedusers'),
               (Allow, 'group:editors', 'edit'),
               (Allow, 'g:admin', ALL_PERMISSIONS)]

    def __init__(self, request):
        pass


class NoAuthenticationRoot(Root):
    def __init__(self, request):
        super(NoAuthenticationRoot, self).__init__(request)
        for i, acl in enumerate(self.__acl__):
            self.__acl__[i] = (acl[0], Everyone, acl[2])
