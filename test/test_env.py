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

from cityhall import Settings, _validate_path
from cityhall.errors import InvalidCall, NoDefaultEnv
from unittest import TestCase
from helper_funcs import (
    build,
    TestRaisesLoggedOutMixin,
    TestFailureIsReturnedMixin,
)
from mock import patch
from datetime import datetime


class TestEnv(
    TestCase,
    TestRaisesLoggedOutMixin,
    TestFailureIsReturnedMixin,
):
    def setUp(self):
        self.url = 'http://not.a.real.url/api/'
        self.name = 'test_user'
        self.password = ''
        self.value = 'some value'
        self.protect = True
        self.get_value = build(
            update={'value': self.value, 'protect': self.protect}
        )
        self.get_children = build(
            update={
                "path": "/abc/",
                "children": [
                    {
                        "override": "",
                        "path": "/abc/val1/",
                        "id": 9,
                        "value": "1000",
                        "protect": False,
                        "name": "val1"
                    },
                    {
                        "override": "test_user",
                        "path": "/abc/val1/",
                        "id": 12,
                        "value": "50",
                        "protect": False,
                        "name": "val1"
                    }
                ]
            }
        )
        self.get_history = build(
            update={
                "History": [
                    {
                        "active": False,
                        "override": "",
                        "id": 12,
                        "value": "1000",
                        "datetime": datetime.now(),
                        "protect": False,
                        "name": "abc",
                        "author": "cityhall"
                    },
                    {
                        "active": True,
                        "override": "",
                        "id": 12,
                        "value": "50",
                        "datetime": datetime.now(),
                        "protect": False,
                        "name": "abc",
                        "author": "test_dev"
                    }
                ]
            }
        )
        with patch('requests.Session.post') as post:
            with patch('requests.Session.get') as get:
                post.return_value = build()
                get.return_value = build(update={'value': 'dev'})
                self.settings = Settings(self.url, self.name, self.password)

    def test_get_mixins(self):
        call = lambda: self.settings._get_raw('dev', '/abc', None)
        self.failed_call_honored(call, 'requests.Session.get')
        self.logout_honored(call, self.settings)

    @patch('requests.Session.get')
    def test_get_no_override(self, get):
        get.return_value = self.get_value
        value = self.settings.get('/abc')
        get.assert_called_once_with(self.url + 'env/dev/abc/', params=None)
        self.assertEqual(self.value, value)

    @patch('requests.Session.get')
    def test_get_specify_protect(self, get):
        get.return_value = self.get_value
        ret = self.settings.get('/abc', view_raw=True)
        get.assert_called_once_with(self.url + 'env/dev/abc/', params=None)
        self.assertIsInstance(ret, dict)
        self.assertEqual(self.value, ret['value'])
        self.assertEqual(self.protect, ret['protect'])

    @patch('requests.Session.get')
    def test_get_specify_protect_and_override(self, get):
        get.return_value = self.get_value
        ret = self.settings.get('/abc', view_raw=True, override='guest')
        params = {'override': 'guest'}
        get.assert_called_once_with(self.url + 'env/dev/abc/', params=params)
        self.assertIsInstance(ret, dict)
        self.assertEqual(self.value, ret['value'])
        self.assertEqual(self.protect, ret['protect'])

    @patch('requests.Session.get')
    def test_get_with_override(self, get):
        get.return_value = self.get_value
        value = self.settings.get('/abc', override='guest')
        get_url = self.url + 'env/dev/abc/'
        get.assert_called_once_with(get_url, params={'override': 'guest'})
        self.assertEqual(self.value, value)

    @patch('requests.Session.get')
    def test_get_with_env(self, get):
        get.return_value = self.get_value
        value = self.settings.get('/abc', env='qa')
        get.assert_called_once_with(self.url + 'env/qa/abc/', params=None)
        self.assertEqual(self.value, value)

    @patch('requests.Session.get')
    def test_get_with_env_and_override(self, get):
        get.return_value = self.get_value
        value = self.settings.get('/abc', env='qa', override='guest')
        get_url = self.url + 'env/qa/abc/'
        get.assert_called_once_with(get_url, params={'override': 'guest'})
        self.assertEqual(self.value, value)

    @patch('requests.Session.get')
    def test_get_view_children(self, get):
        get.return_value = self.get_children
        children = self.settings.get_children('/abc')
        params = {'viewchildren': True}
        get_url = self.url + 'env/dev/abc/'
        get.assert_called_once_with(get_url, params=params)
        json = self.get_children.json()
        self.assertEqual(children, json['children'])

    @patch('requests.Session.get')
    def test_get_view_children_override(self, get):
        get.return_value = self.get_children
        children = self.settings.get_children('/abc', override='guest')
        params = {'viewchildren': True, 'override': 'guest'}
        get_url = self.url + 'env/dev/abc/'
        get.assert_called_once_with(get_url, params=params)
        json = self.get_children.json()
        self.assertEqual(children, json['children'])

    @patch('requests.Session.get')
    def test_get_view_children_override_env(self, get):
        get.return_value = self.get_children
        children = self.settings.get_children('/abc', override='abc', env='qa')
        params = {'viewchildren': True, 'override': 'abc'}
        get_url = self.url + 'env/qa/abc/'
        get.assert_called_once_with(get_url, params=params)
        json = self.get_children.json()
        self.assertEqual(children, json['children'])

    @patch('requests.Session.get')
    def test_get_view_history(self, get):
        get.return_value = self.get_history
        history = self.settings.get_history('/abc')
        params = {'viewhistory': True}
        get_url = self.url + 'env/dev/abc/'
        get.assert_called_once_with(get_url, params=params)
        json = self.get_history.json()
        self.assertEqual(history, json['History'])

    @patch('requests.Session.get')
    def test_get_view_history_override(self, get):
        get.return_value = self.get_history
        history = self.settings.get_history('/abc', override='abc')
        params = {'viewhistory': True, 'override': 'abc'}
        get_url = self.url + 'env/dev/abc/'
        get.assert_called_once_with(get_url, params=params)
        json = self.get_history.json()
        self.assertEqual(history, json['History'])

    @patch('requests.Session.get')
    def test_get_view_history_override_env(self, get):
        get.return_value = self.get_history
        history = self.settings.get_history('/abc', override='abc', env='qa')
        params = {'viewhistory': True, 'override': 'abc'}
        get_url = self.url + 'env/qa/abc/'
        get.assert_called_once_with(get_url, params=params)
        json = self.get_history.json()
        self.assertEqual(history, json['History'])

    def test_validate_path(self):
        """
        You must specify something that looks like a path.
        It must start with '/', etc.
        """
        with self.assertRaises(InvalidCall):
            _validate_path('abc')
        with self.assertRaises(InvalidCall):
            _validate_path('/abc def')

    @patch('requests.Session.post')
    def test_set(self, post):
        post.return_value = build()
        self.settings.set('dev', '/abc', '', 1000)
        payload = {'value': 1000}
        params = {'override': ''}
        post_url = self.url + 'env/dev/abc/'
        post.assert_called_once_with(post_url, data=payload, params=params)

        call = lambda: self.settings.set('dev', '/abc', '', 1000)
        self.failed_call_honored(call, 'requests.Session.post')
        self.logout_honored(call, self.settings)

    @patch('requests.Session.post')
    def test_set_override(self, post):
        post.return_value = build()
        self.settings.set('dev', '/abc', self.name, 'some value')
        payload = {'value': 'some value'}
        post_url = self.url + 'env/dev/abc/'
        params = {'override': self.name}
        post.assert_called_once_with(post_url, data=payload, params=params)

    @patch('requests.Session.post')
    def test_set_protect(self, post):
        post.return_value = build()
        self.settings.set_protect('dev', '/abc', '', True)
        payload = {'protect': True}
        params = {'override': ''}
        post_url = self.url + 'env/dev/abc/'
        post.assert_called_once_with(post_url, data=payload, params=params)

        call = lambda: self.settings.set_protect('dev', '/abc', '', True)
        self.failed_call_honored(call, 'requests.Session.post')
        self.logout_honored(call, self.settings)

    @patch('requests.Session.post')
    def test_set_protect_override(self, post):
        post.return_value = build()
        self.settings.set_protect('dev', '/abc', self.name, True)
        payload = {'protect': True}
        post_url = self.url + 'env/dev/abc/'
        params = {'override': self.name}
        post.assert_called_once_with(post_url, data=payload, params=params)

    def test_no_default_env_raises_NoDefaultEnv(self):
        self.settings.default_env = None
        with self.assertRaises(NoDefaultEnv):
            self.settings.get('/some_value')
