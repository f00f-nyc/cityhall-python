import requests
from errors import NotLoggedIn, FailedCall
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
        self._ensure_logged_in()

        env_url = self.url + 'auth/user/{}/default/'.format(self.name)
        resp = self.session.get(env_url)
        env = _ensure_okay(resp)
        self.default_env = env['value']

    def set_default_env(self, env):
        self._ensure_logged_in()

        env_url = self.url + 'auth/user/{}/default/'.format(self.name)
        payload = {'env': env}
        resp = self.session.post(env_url, data=payload)
        _ensure_okay(resp)
        self.default_env = env

    def log_out(self):
        if self.logged_in:
            self.session.delete(self.url + 'auth/')
            self.logged_in = None

    def get_env(self, env):
        raise NotImplementedError()

    def create_env(self, env):
        raise NotImplementedError()

    def get(self, path, env=None):
        if self.logged_in:
            env = env or 'dev'
            get_url = self.url + 'env/' + env + path
            resp = requests.get(get_url, cookies=self.cookies)
            return resp.json()


def session_attempt():
    url = 'http://digital-borderlands.herokuapp.com/api/'
    with requests.Session() as session:
        url = _sanitize_url(url)
        auth_url = url + 'auth/'
        data = {'username': 'alex', 'passhash': ''}
        ret = session.post(auth_url, data=data)

        if ret.status_code == 200 and ret.json()['Response'] == 'Ok':
            get_url = url + 'env/dev/Calculator1/test/'
            resp = session.get(get_url)
            ret = resp.json()
            session.delete(auth_url)
            return ret

        raise NotLoggedIn()
