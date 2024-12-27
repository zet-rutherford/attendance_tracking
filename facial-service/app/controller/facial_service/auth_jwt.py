# -*- coding: utf-8 -*-
from flask import request


class JWTError(Exception):
    def __init__(self, error, description, status_code=401, headers=None):
        Exception.__init__(self)
        self.error = error
        self.description = description
        self.status_code = status_code
        self.headers = headers

    def __repr__(self):
        return 'JWTError: %s' % self.error

    def __str__(self):
        return '%s. %s' % (self.error, self.description)

    def to_dict(self):
        rv = dict(())
        rv['status_code'] = self.status_code
        rv['error'] = self.error + '. ' + self.description
        rv['data'] = ''
        return rv


def request_handle():
    auth_header_value = request.headers.get('Authorization', None)
    auth_body_value = request.values.get('Authorization', None)

    if auth_header_value:
        parts = auth_header_value.split()
    elif auth_body_value:
        parts = auth_body_value.split()
    else:
        return None, None

    auth_header_prefix = ['jwt', 'token', 'bearer']

    if parts[0].lower() not in auth_header_prefix:
        raise JWTError('Invalid JWT header', 'Unsupported authorization type')
    elif len(parts) == 1:
        raise JWTError('Invalid JWT header', 'Token missing')
    elif len(parts) > 2:
        raise JWTError('Invalid JWT header', 'Token contains spaces')

    return parts[0], parts[1]
