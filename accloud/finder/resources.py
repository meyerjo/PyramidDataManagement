from pyramid.security import Allow, Everyone, Authenticated, ALL_PERMISSIONS


class Root(object):
    __name__ = None
    __acl__ = [(Allow, Authenticated, 'authenticatedusers'),
               (Allow, 'group:editors', 'edit'),
               (Allow, 'g:admin', ALL_PERMISSIONS)]

    def get_all_groups(self):
        group = []
        for a in self.__acl__:
            str_groupname = str(a[1])
            if not str_groupname.startswith('system.'):
                group.append(str_groupname)
        return group

    def __init__(self, request):
        pass


class NoAuthenticationRoot(Root):
    def __init__(self, request):
        super(NoAuthenticationRoot, self).__init__(request)
        for i, acl in enumerate(self.__acl__):
            self.__acl__[i] = (acl[0], Everyone, acl[2])

    def get_all_groups(self):
        group = []
        for a in self.__acl__:
            str_groupname = str(a[1])
            if not str_groupname.startswith('system.'):
                group.append(str_groupname)
        return group
