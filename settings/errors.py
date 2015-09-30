class NotLoggedIn(Exception):
    pass


class FailedCall(Exception):
    pass


class InvalidCall(FailedCall):
    pass
