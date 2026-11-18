"""Errors with messages written for whoever reads them: a person or Claude."""


class LaiError(Exception):
    """Base error. The CLI prints the message and exits with code 2."""


class ServerUnavailable(LaiError):
    pass


class ContextOverflow(LaiError):
    pass


class EmptyAnswer(LaiError):
    pass
