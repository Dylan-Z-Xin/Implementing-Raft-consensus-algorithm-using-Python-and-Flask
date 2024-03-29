import json
import logging
import os

from flask import Flask, jsonify, request
from gevent import monkey
from timer_thread import TimerThread

from cluster import Cluster

monkey.patch_all()

logging.basicConfig(format='%(asctime)s-%(levelname)s:%(message)s', datefmt='%H:%M:%S', level=logging.INFO)

NODE_ID = int(os.environ.get('NODE_ID'))
cluster = Cluster()
node = cluster[NODE_ID]
timer_thread = TimerThread(NODE_ID)


def create_app():
    raft = Flask(__name__)
    timer_thread.start()
    return raft


app = create_app()


@app.route('/raft/vote', methods=['POST'])
def request_vote():
    vote_request = request.get_json()
    result = timer_thread.vote(json.loads(vote_request))
    return jsonify(result)


@app.route('/raft/heartbeat', methods=['POST'])
def heartbeat():
    leader = request.get_json()
    logging.info(f'{timer_thread} got heartbeat from leader: {leader}')
    d = {"alive": True, "node": node}
    timer_thread.become_follower()
    return jsonify(d)


@app.route('/')
def hello_raft():
    return f'raft cluster:{cluster}'


if __name__ == '__main__':
    create_app()
    app.run()
