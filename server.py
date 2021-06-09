import json
import logging
import sys

import trio

from trio_websocket import ConnectionClosed
from trio_websocket import serve_websocket

buses = {}

logger = logging.getLogger('server')


async def receive_bus_coordinates(request):
    ws = await request.accept()

    while True:
        try:
            received_message = await ws.get_message()
            bus_info = json.loads(received_message)

            logger.debug(f'Received message:{bus_info}')

            buses.update({bus_info['busId']: bus_info})

        except ConnectionClosed:
            break


async def send_buses(ws, bounds):
    while True:
        buses_location = [
            coords
            for coords
            in buses.values()
            if is_inside(bounds, coords['lat'], coords['lng'])
        ]
        browser_msg = {
            'msgType': 'Buses',
            'buses': buses_location
        }
        try:
            await ws.send_message(json.dumps(browser_msg, ensure_ascii=True))
            logger.debug(f'Talk to browser:{browser_msg["buses"]}')
            logger.debug(f'{len(buses_location)} buses inside bounds')

            await trio.sleep(2)

        except ConnectionClosed:
            break


async def listen_browser(ws, bounds):
    while True:
        try:
            message = await ws.get_message()
            new_bounds = json.loads(message)
            bounds.update(new_bounds['data'])

            logger.debug(new_bounds)
        except ConnectionClosed:
            break


async def talk_to_browser(request):
    ws = await request.accept()
    bounds = {}
    async with trio.open_nursery() as nursery:
        nursery.start_soon(send_buses, ws, bounds)
        nursery.start_soon(listen_browser, ws, bounds)


def is_inside(bounds, lat, lng):
    if not bounds:
        return
    south_lat = bounds['south_lat']
    north_lat = bounds['north_lat']
    west_lng = bounds['west_lng']
    east_lng = bounds['east_lng']
    return south_lat <= lat <= north_lat and west_lng <= lng <= east_lng


async def main():
    logging.getLogger('trio-websocket').setLevel(logging.WARNING)
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(levelname)s:%(name)s:%(message)s'
    )

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
