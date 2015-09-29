from settings import (
    Settings,
    _sanitize_url,
    _hash_password,
    _ensure_okay
)
from settings.errors import FailedCall
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
    TestFailureIsReturnedMixin
):
    """
    This class the the authentication for the library.
    Authentication is done at the start, and maintained in the session.
    """
    def setUp(self):
        self.url = 'http://not.a.real.url/api/'
        self.username = 'test_user'

    @patch('requests.Session.get')
    @patch('settings.requests.Session.post')
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
    @patch('settings.requests.Session.post')
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
    @patch('settings.requests.Session.post')
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
    @patch('settings.requests.Session.post')
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
    TestFailureIsReturnedMixin
):
    def setUp(self):
        self.url = 'http://not.a.real.url/api/'
        self.username = 'test_user'
        self.password = ''
        self.settings = Settings(self.url, self.username, self.password)

    def test_can_get_environment(self):
        """
        A user is able to get details for an environment
        """
        self.assertTrue(False)

        call = lambda x: self.settings.get_env('dev')
        self.failed_call_honored(call, 'Session.get')
        self.logout_honored(call, self.settings)

    def test_can_create_environment(self):
        """
        A user is able to create an environment
        """
        self.assertTrue(False)

        call = lambda x: self.settings.create_env('dev')
        self.failed_call_honored(call, 'Session.post')
        self.logout_honored(call, self.settings)