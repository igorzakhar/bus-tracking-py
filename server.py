import logging
import sys

import trio
from trio_websocket import serve_websocket, ConnectionClosed


async def receive_coords(request):
    ws = await request.accept()

    while True:
        try:
            message = await ws.get_message()
            logging.debug(f'Received message: {message}')
        except ConnectionClosed:
            break


async def main():
    logging.getLogger('trio-websocket').setLevel(logging.WARNING)
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')

    await serve_websocket(receive_coords, '127.0.0.1', 9000, ssl_context=None)


if __name__ == '__main__':
    try:
        trio.run(main)
    except KeyboardInterrupt:
        sys.exit()
