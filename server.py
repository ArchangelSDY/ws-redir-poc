#!/usr/bin/env python
from http import HTTPStatus
import sys
import asyncio
import websockets
import redis

port = sys.argv[1]
ip = sys.argv[2]
rc = redis.Redis(host='localhost', port=6379)


def process_request(path, request_headers):
    print('Got request')
    least_used = rc.zrange('poc', 0, 0)
    if len(least_used) == 0:
        print('No redirection')
        return None

    least_used = least_used[0].decode('utf-8')
    if least_used == ip:
        print('No redirection')
        return None

    url = 'ws://{0}'.format(least_used)
    print('Redirect to', url)
    return HTTPStatus.TEMPORARY_REDIRECT, (('Location', url),), b''


async def echo(websocket, path):
    print('Upgraded')
    rc.zincrby('poc', 1, ip)
    try:
        async for message in websocket:
            await websocket.send(message)
    except websockets.exceptions.ConnectionClosed:
        print('Connection closed')
        rc.zincrby('poc', -1, ip)

asyncio.get_event_loop().run_until_complete(
        websockets.serve(echo, '0.0.0.0', port, process_request=process_request))
asyncio.get_event_loop().run_forever()
