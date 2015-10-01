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

from mock import MagicMock, patch
from settings.errors import NotLoggedIn, FailedCall


def build(reply='Ok', message=None, status_code=200, update=None):
    """
    Builds a response from the server to be used when mocking.
    post.return_value = build(update={'value': '123', 'protect': False}

    :param reply: The response, default to 'Ok'.
    :param message: If reply is 'Failure', this contains an explanation
    :param status_code: Status code of the http request, default to 200
    :param update: What to update the json() value with
    :return: the object itself
    """
    ret = MagicMock()
    ret.status_code = status_code
    json = {'Response': reply}
    if message:
        json['Message'] = message
    if update:
        json.update(update)
    ret.json.return_value = json
    return ret


class TestRaisesLoggedOutMixin(object):
    """
    Tets that if the user is logged out, a NotLoggedIn error is raised
    """

    def logout_honored(self, call, settings):
        """
        For the settings object, the lambda call() should raise NotLoggedIn
        if the user is logged out.
        """
        with patch('requests.Session.delete') as delete:
            request = delete.return_value
            request.return_value = build()
            settings.log_out()
        with self.assertRaises(NotLoggedIn):
            call()


class TestFailureIsReturnedMixin(object):
    """
    Tests that if the call doesn't succeed, a FailedCall error is raised
    """

    def failed_call_honored(self, call, mocked_call):
        """
        For the lambda call() which wraps a request mocked_call, if the
        result is a failure, that should be returned.

        :param call: What is to be called.  E.x. lambda x: settings.get('/val')
        :param mocked_call: What it actually wraps.  E.x. 'Settings.get'
        """
        with patch(mocked_call) as mocked:
            request = mocked.return_value
            request.return_value = build(reply='Failure', message='Some message')
            with self.assertRaises(FailedCall):
                call()
