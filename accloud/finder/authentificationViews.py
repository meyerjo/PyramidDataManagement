import logging

import jsonpickle
from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render
from pyramid.response import Response
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

    @view_config(route_name='usermanagement', renderer='template/usermanagement.pt', permission='nooneshouldhavethispermission')
    @view_config(route_name='usermanagement_action', renderer='json', permission='nooneshouldhavethispermission')
    def usermanagement(self):
        log = logging.getLogger(__name__)
        error = None
        if self.request.matched_route.name == 'usermanagement_action':
            log.debug('Matched the action route, will process the request')
            matchdict = self.request.matchdict
            params = dict(self.request.params)

            if 'roles' in params and isinstance(params['roles'], unicode):
                params['roles'] = jsonpickle.decode(params['roles'])

            if matchdict['action'] == 'updateuser':
                try:
                    log.info('Update user {0}'.format(matchdict['id']))
                    self.request.registry.settings['usermanager'].update_user(matchdict['id'],
                                                                             params['username'],
                                                                             params['useractive'],
                                                                             params['roles'])
                    return {'error': None}
                except BaseException as e:
                    log.warning(e.message)
                    return {'error': str(e.message)}
            elif matchdict['action'] == 'deleteuser':
                # let the request run through
                if matchdict['id'] == params['username']:
                    try:
                        log.info('Delete user: {0}'.format(matchdict['id']))
                        self.request.registry.settings['usermanager'].delete_user(matchdict['id'])
                    except BaseException as e:
                        log.warning(e.message)
                        error = str(e.message)
                    return {'error': error}
            elif matchdict['action'] == 'adduser':
                if matchdict['id'] == 'newuser':
                    try:
                        log.info('Try to add user "{0}" now'.format(params['username']))
                        self.request.registry.settings['usermanager'].add_user(params['username'],
                                                                               params['username'].lower(),
                                                                               params['useractive'],
                                                                               params['roles'])
                    except BaseException as e:
                        log.warning(e.message)
                        error = str(e.message)
                    return {'error': error}

        users = self.request.registry.settings['usermanager'].allUsers()
        aclgroups = self.request.root.get_all_groups()
        renderdict =  dict(folders=[], files=dict(),
                           logged_in=self.logged_in, users=users,
                           request=self.request, aclgroups=aclgroups,
                           error=error)
        return renderdict
