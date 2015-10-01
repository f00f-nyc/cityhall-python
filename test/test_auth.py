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

from cityhall import (
    Settings,
    _sanitize_url,
    _hash_password,
    _ensure_okay
)
from cityhall.errors import FailedCall, InvalidCall
from unittest import TestCase
from helper_funcs import (
    build,
    TestRaisesLoggedOutMixin,
    TestFailureIsReturnedMixin,
)
from mock import patch


class TestSettingsFuncs(TestCase):
    def test_sanitize_url(self):
        self.assertEqual('http://url/', _sanitize_url('http://url'))
        self.assertEqual('http://url/', _sanitize_url('http://url/'))

    def test_hash_password(self):
        self.assertEqual(
            '', _hash_password(''),
            "by convention, empty strings are passed as-is"
        )
        self.assertNotEqual('abc', _hash_password('abc'))
        self.assertNotEqual('', _hash_password('abc'))

    def test_ensure_okay(self):
        self.assertIsInstance(_ensure_okay(build()), dict)
        with self.assertRaises(FailedCall):
            _ensure_okay(build(status_code=400))
        with self.assertRaises(FailedCall):
            _ensure_okay(build(reply='Failure', message='abc'))


class TestAuthenticationAndDefaultEnvs(
    TestCase,
    TestRaisesLoggedOutMixin,
    TestFailureIsReturnedMixin,
):
    """
    This class the the authentication for the library.
    Authentication is done at the start, and maintained in the session.
    """
    def setUp(self):
        self.url = 'http://not.a.real.url/api/'
        self.username = 'test_user'

    @patch('requests.Session.get')
    @patch('requests.Session.post')
    def test_no_password_is_honored(self, post, get):
        """
        By convention, no password passes an empty string
        """
        post.return_value = build()
        get.return_value = build(update={'value': 'dev'})
        Settings(self.url, self.username, '')

        auth_url = self.url + 'auth/'
        post.assert_called_once_with(
            auth_url,
            data={'username': self.username, 'passhash': ''}
        )

    @patch('requests.Session.get')
    @patch('requests.Session.post')
    def test_password_is_hashed(self, post, get):
        """
        A password is passed in as plaintext and is hashed before the post
        """
        post.return_value = build()
        get.return_value = build(update={'value': 'dev'})
        Settings(self.url, self.username, 'abc')

        auth_url = self.url + 'auth/'
        post.assert_called_once_with(
            auth_url,
            data={'username': self.username, 'passhash': _hash_password('abc')}
        )

    @patch('requests.Session.get')
    @patch('requests.Session.post')
    def test_default_env_is_retrieved(self, post, get):
        """
        Upon logging in, the default environment is retrieved
        """
        post.return_value = build()
        get.return_value = build(update={'value': 'dev'})
        settings = Settings(self.url, self.username, 'abc')
        get.asssert_called_once_with(
            self.url + 'auth/user/' + self.username + '/default/'
        )
        self.assertEqual('dev', settings.default_env)

        self.failed_call_honored(
            settings.get_default_env, 'requests.Session.get'
        )
        self.logout_honored(settings.get_default_env, settings)

    @patch('requests.Session.delete')
    @patch('requests.Session.get')
    @patch('cityhall.requests.Session.post')
    def test_logging_out(self, post, get, delete):
        """
        Logging out hits the correct url
        """
        post.return_value = build()
        get.return_value = build(update={'value': 'dev'})
        delete.return_value = build()
        settings = Settings(self.url, self.username, '')
        settings.log_out()

        delete.assert_called_once_with(self.url + 'auth/')
        self.assertFalse(settings.logged_in)

    @patch('requests.Session.post')
    @patch('requests.Session.get')
    def test_setting_default_env(self, get, post):
        """
        A user should be able to set the environment, also.
        This test is here for completeness sake, since the call to get
        the default environment is part creating the Settings() class
        """
        get.return_value = build(update={'value': 'dev'})
        post.return_value = build(message='Updated default env')
        settings = Settings(self.url, self.username, '')
        settings.set_default_env('abc')

        post.assert_called_with(
            self.url + 'auth/user/' + self.username + '/default/',
            data={'env': 'abc'}
        )
        self.assertEqual('abc', settings.default_env)

        call = lambda: settings.set_default_env('abc')
        self.failed_call_honored(call, 'requests.Session.post')
        self.logout_honored(call, settings)


class TestAuthEnvironments(
    TestCase,
    TestRaisesLoggedOutMixin,
    TestFailureIsReturnedMixin,
):
    def setUp(self):
        self.url = 'http://not.a.real.url/api/'
        self.name = 'test_user'
        self.password = ''
        with patch('requests.Session.post') as post:
            with patch('requests.Session.get') as get:
                post.return_value = build()
                get.return_value = build(update={'value': 'dev'})
                self.settings = Settings(self.url, self.name, self.password)

    @patch('requests.Session.get')
    def test_can_get_environment(self, get):
        """
        A user is able to get details for an environment
        """
        get.return_value = build(
            update={'Users': {'test_user': 4, 'user2': 1, 'guest': 1}}
        )
        env_users = self.settings.get_env('dev')

        self.assertEqual(3, len(env_users))
        self.assertIn('test_user', env_users)
        self.assertEqual(4, env_users['test_user'])

        call = lambda: self.settings.get_env('dev')
        self.failed_call_honored(call, 'requests.Session.get')
        self.logout_honored(call, self.settings)

    @patch('requests.Session.post')
    def test_can_create_environment(self, post):
        """
        A user is able to create an environment
        """
        post.return_value = build()
        self.settings.create_env('dev2')
        post.assert_called_once_with(self.url + 'auth/env/dev2/')

        call = lambda: self.settings.create_env('dev')
        self.failed_call_honored(call, 'requests.Session.post')
        self.logout_honored(call, self.settings)


class TestAuthUsers(
    TestCase,
    TestRaisesLoggedOutMixin,
    TestFailureIsReturnedMixin,
):
    def setUp(self):
        self.url = 'http://not.a.real.url/api/'
        self.name = 'test_user'
        self.password = ''
        with patch('requests.Session.post') as post:
            with patch('requests.Session.get') as get:
                post.return_value = build()
                get.return_value = build(update={'value': 'dev'})
                self.settings = Settings(self.url, self.name, self.password)

    @patch('requests.Session.get')
    def test_get_user(self, get):
        """
        Get information about a user, his permissions on all environments
        """
        get.return_value = build(update={
            'Environments': {'dev': 4, 'auto': 1, 'users': 1}
        })
        rights = self.settings.get_user('test_user')

        self.assertEqual(3, len(rights))
        self.assertIn('dev', rights)
        self.assertEqual(4, rights['dev'])

        get.asssert_called_once_with(self.url + 'auth/user/test_user/')
        call = lambda: self.settings.get_user('test_user')
        self.failed_call_honored(call, 'requests.Session.get')
        self.logout_honored(call, self.settings)

    @patch('requests.Session.post')
    def test_create_user(self, post):
        """
        Create a user
        """
        post.return_value = build()
        self.settings.create_user('user2', '')
        auth_url = self.url + 'auth/user/user2/'
        post.assert_called_with(auth_url, data={'passhash': ''})

        self.settings.create_user('user2', 'abc')
        abc_hash = _hash_password('abc')
        post.assert_called_with(auth_url, data={'passhash': abc_hash})

        call = lambda: self.settings.create_user('user2', 'abc')
        self.failed_call_honored(call, 'requests.Session.post')
        self.logout_honored(call, self.settings)

    @patch('requests.Session.put')
    def test_update_password(self, put):
        """
        Update your own password
        """
        put.return_value = build()
        self.settings.update_password('')
        auth_url = self.url + 'auth/user/' + self.name + '/'
        put.assert_called_with(auth_url, data={'passhash': ''})

        self.settings.update_password('abc')
        abc_hash = _hash_password('abc')
        put.assert_called_with(auth_url, data={'passhash': abc_hash})

        call = lambda: self.settings.update_password('abc')
        self.failed_call_honored(call, 'requests.Session.put')
        self.logout_honored(call, self.settings)

    @patch('requests.Session.delete')
    def test_delete_user(self, delete):
        """
        Delete a user
        """
        delete.return_value = build()
        self.settings.delete_user('other_user')
        auth_url = self.url + 'auth/user/other_user/'
        delete.assert_called_once_with(auth_url)

        call = lambda: self.settings.delete_user('other_user')
        self.failed_call_honored(call, 'requests.Session.delete')
        self.logout_honored(call, self.settings)


class TestAuthGrant(
    TestCase,
    TestFailureIsReturnedMixin,
    TestRaisesLoggedOutMixin
):
    def setUp(self):
        self.url = 'http://not.a.real.url/api/'
        self.name = 'test_user'
        self.password = ''
        with patch('requests.Session.post') as post:
            with patch('requests.Session.get') as get:
                post.return_value = build()
                get.return_value = build(update={'value': 'dev'})
                self.settings = Settings(self.url, self.name, self.password)

    def test_grant_rights_validation(self):
        """
        Rights should be a value of 0, 1, 2, 3, or 4
        """
        with self.assertRaises(InvalidCall):
            self.settings.grant_rights('dev', 1, 0)
        with self.assertRaises(InvalidCall):
            self.settings.grant_rights(1, 'abc', 0)
        with self.assertRaises(InvalidCall):
            self.settings.grant_rights('dev', 'abc', 5)
        with self.assertRaises(InvalidCall):
            self.settings.grant_rights('dev', 'abc', -1)
        with self.assertRaises(InvalidCall):
            self.settings.grant_rights('dev', 'abc', 1.1)

    @patch('requests.Session.post')
    def test_grant_rights(self, post):
        post.return_value = build()
        self.settings.grant_rights('dev', 'abc', 2)

        post.assert_called_once_with(
            self.url + 'auth/grant/',
            data={
                'env': 'dev',
                'user': 'abc',
                'rights': 2
            }
        )
        call = lambda: self.settings.grant_rights('dev', 'abc', 2)
        self.failed_call_honored(call, 'requests.Session.post')
        self.logout_honored(call, self.settings)
