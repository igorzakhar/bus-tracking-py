import json
import logging
import sys

import trio

from trio_websocket import ConnectionClosed
from trio_websocket import serve_websocket

buses = {}

async def receive_bus_coordinates(request):

    ws = await request.accept()

    while True:

        try:
            received_message = await ws.get_message()
            bus_info = json.loads(received_message)

            logging.debug(f'Received message: {bus_info}')

            buses.update({bus_info['busId']: bus_info})

        except ConnectionClosed:
            break


async def talk_to_browser(request):
    ws = await request.accept()

    while True:
        buses_location = [coords for coords in buses.values()]
        browser_msg = {
            'msgType': 'Buses',
            'buses': buses_location
        }
        try:
            await ws.send_message(json.dumps(browser_msg, ensure_ascii=True))
            logging.debug(f'Talk to browser: {browser_msg["buses"]}')

            await trio.sleep(0.5)

        except ConnectionClosed:
            break


async def main():
    logging.getLogger('trio-websocket').setLevel(logging.WARNING)
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')

    async with trio.open_nursery() as nursery:
        nursery.start_soon(
            serve_websocket,
            receive_bus_coordinates,
            '127.0.0.1',
            8080,
            None
        )
        nursery.start_soon(
            serve_websocket,
            talk_to_browser,
            '127.0.0.1',
            8000,
            None
        )


if __name__ == '__main__':
    try:
        trio.run(main)
    except KeyboardInterrupt:
        sys.exit()
