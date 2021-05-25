import itertools
import json
import logging
import os
import sys

import trio

from trio_websocket import ConnectionClosed
from trio_websocket import open_websocket_url


def load_routes(directory_path='routes'):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)


async def run_bus(url, bus_id, route):
    coordinates = route['coordinates']
    route_cycle = itertools.cycle(coordinates)

    try:
        async with open_websocket_url(url) as ws:
            while True:
                bus_coords = next(route_cycle)
                lat, lng = bus_coords[0], bus_coords[1]
                coordinates = {
                    'busId': f'{route["name"]}',
                    'lat': lat,
                    'lng': lng,
                    'route': route['name']
                }

                message = json.dumps(coordinates, ensure_ascii=True)
                await ws.send_message(message)
                logging.debug(f'Sent message: {coordinates}')

                await trio.sleep(1)

    except OSError as ose:
        logging.exception(ose, exc_info=False)
    except ConnectionClosed:
        desc = f'Connection Closed {ws.local.address}:{ws.local.port}'
        logging.exception(desc, exc_info=False)


async def main():
    logging.getLogger('trio-websocket').setLevel(logging.WARNING)
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')

    url = 'ws://127.0.0.1:8080'

    async with trio.open_nursery() as nursery:
        for route in load_routes():
            bus_id = route['name']
            nursery.start_soon(run_bus, url, bus_id, route)


if __name__ == '__main__':
    try:
        trio.run(main)
    except (KeyboardInterrupt, trio.MultiError):
        sys.exit()
