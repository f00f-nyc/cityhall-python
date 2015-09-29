from settings import Settings, session_attempt
from unittest import TestCase
from mock import patch, MagicMock
from helper_funcs import build


class TestCall(TestCase):
    @patch('requests.Session.delete')
    @patch('requests.Session.get')
    @patch('requests.Session.post')
    def test_session(self, post, get, delete):
        post.return_value = build()
        get.return_value = build(update={'value': '1', 'protect': False})
        delete.return_value = build()
        session_attempt()

    def test_please_work(self):
        # settings = Settings('http://digital-borderlands.herokuapp.com/api', 'alex', '')
        # get = settings.get('/Calculator1/test/', env='dev')
        # print get
        # settings.log_out()
        pass
