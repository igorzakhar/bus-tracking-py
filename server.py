import json
import logging
import sys

from dataclasses import dataclass
from dataclasses import asdict

import trio
from trio_websocket import ConnectionClosed
from trio_websocket import serve_websocket

buses = {}

logger = logging.getLogger('server')


@dataclass
class Bus:
    busId: int
    lat: float
    lng: float
    route: str


@dataclass
class WindowBounds:
    south_lat: float = 0
    north_lat: float = 0
    west_lng: float = 0
    east_lng: float = 0

    def is_inside(self, lat, lng):
        south_lat = self.south_lat
        north_lat = self.north_lat
        west_lng = self.west_lng
        east_lng = self.east_lng
        return south_lat <= lat <= north_lat and west_lng <= lng <= east_lng

    def update(self, south_lat, north_lat, west_lng, east_lng):
        self.south_lat = south_lat
        self.north_lat = north_lat
        self.west_lng = west_lng
        self.east_lng = east_lng


async def receive_bus_coordinates(request):
    ws = await request.accept()

    while True:
        try:
            received_message = await ws.get_message()
            bus_info = json.loads(received_message)

            bus = Bus(**bus_info)
            buses.update({bus.busId: bus})

            logger.debug(f'Received message:{asdict(bus)}')

        except ConnectionClosed:
            break


async def send_buses(ws, bounds):
    while True:
        buses_location = [
            asdict(bus)
            for bus
            in buses.values()
            if bounds.is_inside(bus.lat, bus.lng)
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
            bounds.update(**new_bounds.get('data'))

            logger.debug(new_bounds)
        except ConnectionClosed:
            break


async def talk_to_browser(request):
    ws = await request.accept()
    bounds = WindowBounds()
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
