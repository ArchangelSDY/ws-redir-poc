#!/usr/bin/env python
import argparse
from http import HTTPStatus
import sys
from datetime import datetime
import asyncio
import websockets
import redis

parser = argparse.ArgumentParser()
parser.add_argument('--redis-host', dest='redis_host', required=True)
parser.add_argument('--redis-port', dest='redis_port', type=int, required=True)
parser.add_argument('--redis-password', dest='redis_password')
parser.add_argument('--host', dest='host', required=True)
args = parser.parse_args()

rc = redis.Redis(host=args.redis_host, port=args.redis_port, password=args.redis_password)
rc.zadd('poc', { args.host: 0})

def process_request(path, request_headers):
    print('Got request')
    least_used = rc.zrange('poc', 0, 0)
    if len(least_used) == 0:
        print('No redirection')
        return None

    least_used = least_used[0].decode('utf-8')
    if least_used == args.host:
        print('No redirection')
        return None

    url = 'http://{0}'.format(least_used)
    print('Redirect to', url)
    return HTTPStatus.TEMPORARY_REDIRECT, (('Location', url),), b''


async def echo(websocket, path):
    print('Upgraded')
    rc.zincrby('poc', 1, args.host)
    try:
        for k, v in websocket.request_headers.raw_items():
            await websocket.send('{0}: {1}\n'.format(k, v))

        while True:
            await websocket.send('[{0}] You are on {1}\n'.format(str(datetime.now()), args.host))
            await asyncio.sleep(10)
    except websockets.exceptions.ConnectionClosed:
        print('Connection closed')
        rc.zincrby('poc', -1, args.host)

asyncio.get_event_loop().run_until_complete(
        websockets.serve(echo, '0.0.0.0', 80, process_request=process_request, ping_interval=None))
asyncio.get_event_loop().run_forever()
