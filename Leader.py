import time
from random import randrange

import grequests
from NodeState import NodeState
from client import Client
from cluster import HEART_BEAT_INTERVAL, ELECTION_TIMEOUT_MAX
import logging

from monitor import send_state_update, send_heartbeat

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%H:%M:%S', level=logging.INFO)


class Leader(NodeState):
    def __init__(self, candidate):
        super(Leader, self).__init__(candidate.node)
        self.current_term = candidate.current_term
        self.commit_index = candidate.commit_Index
        self.last_applied_index = candidate.last_applied_index
        self.entries = candidate.entries
        self.stopped = False
        self.followers = [peer for peer in self.cluster if peer != self.node]
        self.election_timeout = float(randrange(ELECTION_TIMEOUT_MAX / 2, ELECTION_TIMEOUT_MAX))

    def heartbeat(self):
        while not self.stopped:
            logging.info(f'{self} send heartbeat to followes')
            logging.info('========================================================================')
            send_heartbeat(self, HEART_BEAT_INTERVAL)
            client = Client()
            with client as session:
                posts = [
                    grequests.post(f'http://{peer.uri}/raft/heartbeat', json=self.node, session=session)
                    for peer in self.followers
                ]
                for response in grequests.map(posts, gtimeout=HEART_BEAT_INTERVAL):
                    if response is not None:
                        logging.info(f'{self} got heartbeat from follower: {response.json()}')
                    else:
                        logging.info(f'{self} got heartbeat from follower:None')
            logging.info('========================================================================')
            time.sleep(HEART_BEAT_INTERVAL)

    def __repr__(self):
        return f'{type(self).__name__, self.node.id, self.current_term}'
