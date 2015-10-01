# Copyright 2015 Digital Borderlands Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License, version 3,
# as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import requests
from errors import NotLoggedIn, FailedCall, InvalidCall
import hashlib
from six import text_type


def _sanitize_url(url):
    return url if url[-1] == '/' else url + '/'


def _hash_password(password):
    """
    Return the City Hall hash for the a given password

    :param password: the plaintext password
    :return: md5 hashed password
    """
    if not password:
        return ''

    md5 = hashlib.md5()
    md5.update(password)
    return text_type(md5.hexdigest())


def _ensure_okay(resp):
    if resp.status_code != 200:
        raise FailedCall("Status code not 200: {}".format(resp.status_code))
    ret = resp.json()
    if ret['Response'] == 'Ok':
        return ret
    raise FailedCall(ret.get('Message', 'No message given for failure'))


def _validate_path(path):
    if path[0] != '/' or path.find(' ') > 0:
        raise InvalidCall("Given path is invalid")


class Settings(object):
    def __init__(self, url, username, password):
        self.session = requests.Session()
        self.url = _sanitize_url(url)
        self.name = username
        self.logged_in = False

        auth_url = self.url + 'auth/'
        passhash = _hash_password(password)
        payload = {'username': self.name, 'passhash': passhash}
        resp = self.session.post(auth_url, data=payload)
        _ensure_okay(resp)

        self.logged_in = True
        self.default_env = None
        self.get_default_env()

    def _ensure_logged_in(self):
        if not self.logged_in:
            raise NotLoggedIn()

    def get_default_env(self):
        """
        Returns the default environment for this user. If you use get()
        without specifying 'env', it will use this environment
        """
        self._ensure_logged_in()

        env_url = self.url + 'auth/user/{}/default/'.format(self.name)
        resp = self.session.get(env_url)
        env = _ensure_okay(resp)
        self.default_env = env['value']

    def set_default_env(self, env):
        """
        Sets the default environment.  This will be honored by the call to
        get() without specifying 'env'.

        Note that no checking is done to make sure that the environment
        specified exists or that the user has read permissions to it.
        Subsequent calls to get() might fail in that case.

        :param env: the environment to set as default.
        """
        self._ensure_logged_in()

        env_url = self.url + 'auth/user/{}/default/'.format(self.name)
        payload = {'env': env}
        resp = self.session.post(env_url, data=payload)
        _ensure_okay(resp)
        self.default_env = env

    def log_out(self):
        """
        Logs the user out. Future calls to the library will raise NotLoggedIn.
        This function is idempotent.
        """
        if self.logged_in:
            self.session.delete(self.url + 'auth/')
            self.logged_in = None

    def get_env(self, env):
        """
        Gets information for the given environment.  For example,
        users who have permissions to it, and their permission level.

        Note that Read permissions are required for this to work.

        :param env: The environment to look at.
        :return: List of users and their read permissions
        """
        self._ensure_logged_in()
        env_url = self.url + 'auth/env/' + env + '/'
        resp = self.session.get(env_url)
        json = _ensure_okay(resp)
        return json['Users']

    def create_env(self, env):
        """
        Allows the user to create an environment. Sets that user up
        as having Grant rights to that environment

        :param env: the environment to create
        """
        self._ensure_logged_in()
        env_url = self.url + 'auth/env/' + env + '/'
        resp = self.session.post(env_url)
        _ensure_okay(resp)

    def get_user(self, user):
        """
        Get user rights for a particular user.

        :param user: the user to query for.
        :return: dict, where keys are environments, and the values are
            rights for that user
        """
        self._ensure_logged_in()
        user_url = self.url + 'auth/user/' + user + '/'
        resp = self.session.get(user_url)
        json = _ensure_okay(resp)
        return json['Environments']

    def create_user(self, user, password):
        """
        Create a user with that password.

        :param user: The user to create
        :param password: The plaintext password
        """
        self._ensure_logged_in()
        user_url = self.url + 'auth/user/' + user + '/'
        payload = {'passhash': _hash_password(password)}
        resp = self.session.post(user_url, data=payload)
        _ensure_okay(resp)

    def update_password(self, password):
        """
        Update your own password.

        :param password: The plaintext password
        """
        self._ensure_logged_in()
        user_url = self.url + 'auth/user/' + self.name + '/'
        payload = {'passhash': _hash_password(password)}
        resp = self.session.put(user_url, data=payload)
        _ensure_okay(resp)

    def delete_user(self, user):
        """
        Delete a user. Deletion can only happen if a user's environments have
        Grant permissions for the current user, or the user has Write
        permissions to the User environment.  If deletion fails, this will
        raise FailedCall.

        :param user: The user to be deleted
        """
        self._ensure_logged_in()
        user_url = self.url + 'auth/user/' + user + '/'
        resp = self.session.delete(user_url)
        _ensure_okay(resp)

    def grant_rights(self, env, user, rights):
        """
        Grant user 'user' 'rights' on environment 'env'.  Note that in order
        to successfully do this, the current user must himself have Grant
        rights on 'env'.

        :param env: string - the environment to set the rights
        :param user: string - the user for whom to set the rights
        :param rights: int - the rights to set. Must be one of 0 - no rights,
            1 - Read, 2 - Read Protected, 3 - Write, 4 - Grant.
        """
        if isinstance(env, text_type) or isinstance(env, str):
            env = text_type(env)
        else:
            raise InvalidCall("Environment must be a string")
        if isinstance(user, text_type) or isinstance(user, str):
            user = text_type(user)
        else:
            raise InvalidCall("User must be a string")
        if not isinstance(rights, int):
            raise InvalidCall("Rights must be an integer 0-4")
        if rights < 0 or rights > 4:
            raise InvalidCall("Rights must be an integer 0-4")

        self._ensure_logged_in()
        grant_url = self.url + 'auth/grant/'
        payload = {'user': user, 'env': env, 'rights': rights}
        resp = self.session.post(grant_url, data=payload)
        _ensure_okay(resp)

    def _get_raw(self, env, path, params):
        _validate_path(path)
        self._ensure_logged_in()
        env = env or self.default_env
        get_url = _sanitize_url(self.url + 'env/' + env + path)
        resp = self.session.get(get_url, params=params)
        return _ensure_okay(resp)

    def get(self, path, env=None, override=None, view_raw=False):
        params = None if override is None else {'override': override}
        json = self._get_raw(env, path, params)
        return json if view_raw else json['value']

    def get_history(self, path, env=None, override=None):
        params = {} if override is None else {'override': override}
        params['viewhistory'] = True
        json = self._get_raw(env, path, params)
        return json['History']

    def get_children(self, path, env=None, override=None):
        params = {} if override is None else {'override': override}
        params['viewchildren'] = True
        json = self._get_raw(env, path, params)
        return json['children']

    def _set_raw(self, env, path, override, payload):
        _validate_path(path)
        self._ensure_logged_in()
        set_url = _sanitize_url(self.url + 'env/' + env + path)
        params = {'override': override}
        resp = self.session.post(set_url, data=payload, params=params)
        _ensure_okay(resp)

    def set(self, env, path, override, value):
        payload = {'value': value}
        self._set_raw(env, path, override, payload)

    def set_protect(self, env, path, override, protect):
        payload = {'protect': protect}
        self._set_raw(env, path, override, payload)
