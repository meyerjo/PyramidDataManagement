import hashlib
import os

import yaml

from accloud.users import User


class UserManager:
    def __init__(self):
        pass

    @staticmethod
    def createPasswordHash(password, salt=None):
        if not salt:
            salt = os.urandom(16).encode('base_64')
            if salt is None:
                import string
                from random import choice
                chars = string.ascii_lowercase + string.ascii_uppercase + string.digits
                salt = "".join(choice(chars) for _ in xrange(32))

        return dict(salt=salt, password=hashlib.sha512(password + salt).hexdigest())

    @classmethod
    def checkPassword(cls, username, password, salt):
        user = cls.get_username(username)
        if not user:
            return False

        hashdict = UserManager.createPasswordHash(password, salt)
        return user.check_password(hashdict['password'])

    @classmethod
    def get_username(cls, username):
        pass

    @classmethod
    def validate_password(cls, username, password):
        pass

    @classmethod
    def groupfinder(cls, userid, request):
        pass

    def addUser(self, username, password, active, roles):
		pass

    def allUsers(self):
        pass

    def updateUser(self, user_id, username, active, group=None):
        pass




class PythonUserManager(UserManager):
    _USERS = {'editor': 'editor',
              'viewer': 'viewer',
              'johannes': 'meyer'}
    _GROUPS = {'editor': ['group:editors'],
               'johannes': ['g:admin']}

    def __init__(self):
        UserManager.__init__(self)

    @classmethod
    def get_username(cls, username):
        return cls._USERS.get(username)

    @classmethod
    def validate_password(cls, username, password):
        print('{0} {1}'.format(username, password))
        print(cls._USERS)
        return cls._USERS.get(username) == password

    @classmethod
    def groupfinder(cls, userid, request):
        if userid in cls._USERS:
            return cls._GROUPS.get(userid, [])

    def addUser(self, username, password, active, roles):
        self._USERS[username] = password
        self._GROUPS[username] = roles
        print("Warning: Won't save this username for future usage.")

    def allUsers(self):
        return self._USERS


class FileBasedUserManager(UserManager):

    def _load(self):
        if os.path.exists(self._userfile) and os.path.isfile(self._userfile):
            self._customized = True
            with open(self._userfile, "r") as f:
                data = yaml.safe_load(f)
                for name in data.keys():
                    attributes = data[name]
                    apikey = None
                    if "apikey" in attributes:
                        apikey = attributes["apikey"]
                    settings = dict()
                    if "settings" in attributes:
                        settings = attributes["settings"]
                    self._users[name] = User(name, attributes["password"],
                                             attributes["active"], attributes["roles"],
                                             apikey=apikey, settings=settings, salt=attributes["salt"])
        else:
            self._customized = False

    def _save(self, force=False):
        if not self._dirty and not force:
            return

        data = {}
        for name in self._users.keys():
            user = self._users[name]
            data[name] = {
                "password": user._passwordHash,
                "active": user._active,
                "roles": user._roles,
                "apikey": user._apikey,
                "settings": user._settings,
                "salt": user._salt
            }
        with open(self._userfile, "wb") as f:
            yaml.safe_dump(data, f, default_flow_style=False, indent="    ", allow_unicode=True)
            self._dirty = False
        self._load()

    def __init__(self):
        UserManager.__init__(self)
        userfile = "C:/code/users.yaml"
        self._userfile = userfile
        self._users = dict()
        self._customized = None
        self._dirty = False
        self._load()

    def get_username(self, username):
        if self._users is None:
            print('User Array is None')
            return None
        user = self._users.get(username)
        return user

    def validate_password(self, username, password):
        user = self.get_username(username)
        if user is None:
            return False
        userdict = user.asDict()
        hashdict = self.createPasswordHash(password, userdict['salt'])
        return user.check_password(hashdict['password'])

    def groupfinder(self, userid, request):
        user = self.get_username(userid)
        if user is not None:
            user = user.asDict()
            return user['roles']

    def addUser(self, username, password, active, roles):
        passworddict = self.createPasswordHash(password)
        user = User(username, passworddict['password'], active, [], None, None, passworddict['salt'])
        self._users[username] = user
        self._dirty = True
        self._save()

    def updateUser(self, user_id, username, active, roles=None):
        if user_id in self._users:
            user = self._users[user_id]
            user.set_username(user_id, username)
            self._users[username] = user
            if roles is not None:
                user.set_roles(roles)

            if user_id != username:
                del self._users[user_id]
            self._dirty = True
            self._save()


    def allUsers(self):
        return self._users