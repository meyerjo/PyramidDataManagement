class User:
    def __init__(self, username, passwordHash, active, roles, apikey=None, settings=None, salt=None):
        self._username = username
        self._passwordHash = passwordHash
        self._active = active
        self._roles = roles
        self._apikey = apikey
        self._salt = salt

        if not settings:
            settings = dict()
        self._settings = settings

    def asDict(self):
        return {
            "name": self._username,
            "roles": self._roles,
            "apikey": self._apikey,
            "settings": self._settings,
            "salt": self._salt
        }

    def check_password(self, passwordHash):
        return self._passwordHash == passwordHash

    def get_id(self):
        return self.get_name()

    def get_name(self):
        return self._username

    def is_active(self):
        return self._active

    def get_all_settings(self):
        return self._settings

    def get_roles(self):
        return self._roles

    def set_username(self, old_username, new_username):
        if self.get_name() == old_username:
            self._username = new_username

    def set_roles(self, roles):
        for role in roles:
            if (isinstance(role, tuple) or \
                    isinstance(role, list)) and len(role) > 1:
                rolename = role[1]
                if role[0]:
                    self._roles = list(set(self._roles + [rolename]))
                elif rolename in self._roles:
                        self._roles.remove(rolename)
            else:
                self._roles = role
                break


    def get_setting(self, key):
        if not isinstance(key, (tuple, list)):
            path = [key]
        else:
            path = key

        return self._get_setting(path)

    def set_setting(self, key, value):
        if not isinstance(key, (tuple, list)):
            path = [key]
        else:
            path = key
        self._set_setting(path, value)

    def _get_setting(self, path):
        s = self._settings
        for p in path:
            if p in s:
                s = s[p]
            else:
                return None
        return s

    def _set_setting(self, path, value):
        s = self._settings
        for p in path[:-1]:
            if not p in s:
                s[p] = dict()

            if not isinstance(s[p], dict):
                return False

            s = s[p]

        key = path[-1]
        s[key] = value
        return True

    def __repr__(self):
        return "User(id=%s,name=%s,active=%r)" % (self.get_id(), self.get_name(), self.is_active())