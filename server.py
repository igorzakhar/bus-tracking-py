import json
import logging

import trio
from trio_websocket import serve_websocket, ConnectionClosed


async def ws_handler(request):
    ws = await request.accept()
    server_msg = {
        "msgType": "Buses",
        "buses": [
            {"busId": "c790сс", "lat": 55.7500, "lng": 37.600, "route": "120"},
            {"busId": "a134aa", "lat": 55.7494, "lng": 37.621, "route": "67к"},
        ]
    }
    while True:
        try:
            await ws.send_message(json.dumps(server_msg))
            front_msg = await ws.get_message()
            logging.debug(json.loads(front_msg))
        except ConnectionClosed:
            break


async def main():
    logging.getLogger('trio-websocket').setLevel(logging.WARNING)
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')

    await serve_websocket(ws_handler, '127.0.0.1', 8000, ssl_context=None)


trio.run(main)
