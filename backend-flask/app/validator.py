# -*- coding: utf-8 -*-

from app.extensions import config
from app.utils.jwt import jwks_storages, custom_verifier, jwt_verifier


def create_verifier():
    st = jwks_storages.GHTKRemoteJWKSStorages(remote_url=config.AUTH_REMOTE_URL,
                                              reload_interval=config.AUTH_RELOAD_INTERVAL)
    list_verify = [
        # custom_verifier.ClaimAudVerifier(audience='auth', separator=' '),
        custom_verifier.KIDVerifier(),
        custom_verifier.AlgVerifier(),
        custom_verifier.ScopeVerifier()
    ]
    return jwt_verifier.JWTVerifier(jwks_storage=st, list_custom_verifier=list_verify)


verifier = create_verifier


def init():
    global verifier
    verifier = create_verifier()
