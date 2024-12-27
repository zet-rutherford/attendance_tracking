import base64
import json

from jwcrypto import jwt


class JWTVerifier:
    def __init__(self, jwks_storage, list_custom_verifier):
        self.jwks_storage = jwks_storage
        self.list_custom_verifier = list_custom_verifier

    def verify(self, token, allowed_scopes=None):
        et = jwt.JWT()
        try:
            he = self.__getheader(token)
            key = self.jwks_storage.get_key(he['kid'])
            et.deserialize(token, key)
            for v in self.list_custom_verifier:
                if not v.custom_verify(key=key, tok=et, allowed_scopes=allowed_scopes):
                    return False
            return True
        except Exception as e:
            raise e

    @staticmethod
    def __getheader(token):
        d = token.split('.')
        t = d[0] + '=' * (-len(d[0]) % 4)
        h_byte = base64.b64decode(t)
        return json.loads(h_byte)

    def shutdown(self):
        try:
            self.jwks_storage.stop()
        except Exception:
            pass

    def get_client_id(self, token):
        et = jwt.JWT()
        try:
            he = self.__getheader(token)
            key = self.jwks_storage.get_key(he['kid'])
            et.deserialize(token, key)
            d = json.loads(et.claims)
            client_id = d['client_id']
            return client_id
        except Exception as e:
            raise e
