import json
from abc import ABC, abstractmethod

from flask import g


class CustomVerifier(ABC):
    @abstractmethod
    def custom_verify(self, **kwargs):
        pass


class ClaimAudVerifier(CustomVerifier):
    def __init__(self, audience, separator):
        self.audience = audience
        self.separator = separator

    def custom_verify(self, key, tok, allowed_scopes):
        d = json.loads(tok.claims)
        aud = d['aud']
        for i in aud.split(self.separator):
            if i == self.audience:
                return True
        return False


class KIDVerifier(CustomVerifier):
    def custom_verify(self, key, tok, allowed_scopes):
        d = json.loads(tok.claims)
        client_id = d['client_id']
        d = json.loads(tok.header)
        header_kid = d['kid']
        return header_kid.startswith(client_id)


class AlgVerifier(CustomVerifier):
    def custom_verify(self, key, tok, allowed_scopes):
        d = key.export(False, True)
        key_alg = d['alg']
        d = json.loads(tok.header)
        token_alg = d['alg']
        return key_alg == token_alg


class ScopeVerifier(CustomVerifier):
    def custom_verify(self, key, tok, allowed_scopes):
        d = json.loads(tok.claims)
        sub = d['sub']
        g.sub = sub
        scopes = d['scp']
        for scope in scopes:
            if scope in allowed_scopes:
                return True
        return False
