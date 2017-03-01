import json

from kazoo.client import KazooClient, KazooState

from logger import logger
from worker.utils import get_config, get_public_hostname
from common_settings import ZK_HOST, ZK_PORT


class DroidZkClient(object):
    def __init__(self):
        self.nodename = None

        host = '{}:{}'.format(ZK_HOST, ZK_PORT)
        zk = KazooClient(host)
        zk.add_listener(self.conn_listener)
        self.zk = zk

    @staticmethod
    def conn_listener(state):
        if state == KazooState.CONNECTED:
            logger.debug('connected...')
        elif state == KazooState.LOST:
            logger.debug('connection lost...')
        elif state == KazooState.SUSPENDED:
            logger.debug('connection suspended...')

    def setup(self):
        logger.debug('Registering onto zookeeper')
        self.zk.start()
        config = get_config()
        value = {
            'thrift_host': get_public_hostname(),
            'thrift_port': config['thrift_port'],
        }
        path = self.zk.create(
            '/droids/running/droid',
            value=json.dumps(value), sequence=True,
            makepath=True, ephemeral=True)
        self.nodename = path.rsplit('/', 1)[1]

    def teardown(self):
        logger.debug('Tearing down DroidZkClient')
        self.zk.stop()


if __name__ == '__main__':
    c = DroidZkClient('droid1')
    c.setup()
    from twisted.internet import reactor

    reactor.addSystemEventTrigger('before', 'shutdown', c.teardown)
    reactor.run()
