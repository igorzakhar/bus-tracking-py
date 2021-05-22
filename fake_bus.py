import json
import logging
import sys
import itertools

import trio
from trio_websocket import open_websocket_url


async def load_bus_route(filename):
    async with await trio.open_file(filename) as fp:
        return await fp.read()


async def send_coords():
    bus_route = json.loads(await load_bus_route('bus_routes/156.json'))
    coordinates = bus_route['coordinates']
    route_cycle = itertools.cycle(coordinates)

    try:
        async with open_websocket_url('ws://127.0.0.1:9000') as ws:
            while True:
                bus_coords = next(route_cycle)
                lat, lng = bus_coords[0], bus_coords[1]
                coordinates = {
                    "busId": "1234567890",
                    "lat": lat,
                    "lng": lng,
                    "route": bus_route["name"]
                }

                await ws.send_message(json.dumps(coordinates))
                logging.debug(f'Sent message: {coordinates}')

                await trio.sleep(1)

    except OSError as ose:
        logging.exception(ose, exec_info=False)


async def main():
    logging.getLogger('trio-websocket').setLevel(logging.WARNING)
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')

    await send_coords()


if __name__ == '__main__':
    try:
        trio.run(main)
    except KeyboardInterrupt:
        sys.exit()
