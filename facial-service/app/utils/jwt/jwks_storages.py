from abc import ABC, abstractmethod

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from jwcrypto import jwk


class JWKSStorages(ABC):

    @abstractmethod
    def get_key(self, key_id):
        pass


class GHTKRemoteJWKSStorages(JWKSStorages):
    def __init__(self, remote_url, reload_interval=0):
        self.remote_url = remote_url
        self.reload_interval = reload_interval
        self.__reload()
        if self.reload_interval > 0:
            self.scheduler = BackgroundScheduler(daemon=True)
            self.scheduler.add_job(self.__reload, 'interval', seconds=reload_interval, id='reload')
            self.scheduler.start()

    def __reload(self):
        r = requests.get(url=self.remote_url)
        data = r.json()
        keys = data['data']['keys']
        jwks = dict()
        for d in keys:
            jwks[d['kid']] = jwk.JWK(**d)
        self.jwks = jwks

    def stop(self):
        if self.scheduler is not None:
            self.scheduler.remove_job('reload')

    def get_key(self, key_id):
        try:
            return self.jwks[key_id]
        except Exception:
            raise Exception('key is not available')
