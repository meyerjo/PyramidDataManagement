import logging

import jsonpickle
from pyramid.httpexceptions import HTTPFound
from pyramid.security import forget, remember
from pyramid.view import view_config, forbidden_view_config

from accloud.finder.security import UserManager

class AuthentificationViews:

    def __init__(self, request):
        self.request = request
        self.logged_in = request.authenticated_userid

    @view_config(route_name='login', renderer='template/login.pt')
    @forbidden_view_config(renderer='template/login.pt')
    def login(self):
        login_url = self.request.resource_url(self.request.context, 'login')
        referrer = self.request.url
        if referrer == login_url:
            referrer = '/'  # never use the login form itself as came_from
        came_from = self.request.params.get('came_from', referrer)
        message = ''
        login = ''
        password = ''
        if 'form.submitted' in self.request.params:
            login = self.request.params['login']
            password = self.request.params['password']
            usermanager = self.request.registry.settings['usermanager']

            if usermanager.validate_password(login, password):
                headers = remember(self.request, login)
                return HTTPFound(location=came_from,
                                 headers=headers)
            message = 'Failed login'

        return dict(
            message=message,
            url=self.request.application_url + '/login',
            came_from=came_from,
            login=login,
            password=password,
        )

    @view_config(route_name='logout')
    def logout(self):
        headers = forget(self.request)
        return HTTPFound(location=self.request.resource_url(self.request.context),
                         headers=headers)

    @view_config(route_name='usermanagement', renderer='template/usermanagement.pt', permission='xedit')
    @view_config(route_name='usermanagement_action', renderer='json', permission='xedit')
    def usermanagement(self):
        log = logging.getLogger(__name__)

        if self.request.matched_route.name == 'usermanagement_action':
            log.debug('Matched the action route, will process the request')
            matchdict = self.request.matchdict
            params = dict(self.request.params)
            if matchdict['action'] == 'updateuser':
                role_array = jsonpickle.decode(params['roles'])
                self.request.registry.settings['usermanager'].updateUser(matchdict['id'],
                                                                         params['username'],
                                                                         params['useractive'],
                                                                         role_array)
            elif matchdict['action'] == 'deleteuser':
                log.info('NOT YET IMPLEMENTED: delete user action')
            elif matchdict['action'] == 'adduser':
                log.info('NOT YET IMPLEMENTED: add user action')
            return {'error': None}



        users = self.request.registry.settings['usermanager'].allUsers()
        aclgroups = self.request.root.get_all_groups()
        return dict(folders=[], files=dict(), logged_in=self.logged_in, users=users, request=self.request, aclgroups=aclgroups)
