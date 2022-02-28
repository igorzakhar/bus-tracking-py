import json
import logging

from contextlib import suppress
from dataclasses import asdict
from dataclasses import dataclass
from json import JSONDecodeError

import asyncclick as click
import trio

from trio_websocket import ConnectionClosed
from trio_websocket import serve_websocket

from schemas import BusSchema
from schemas import WindowBoundSchema


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


def check_message(schema, message):
    return schema().validate(message)


def validate(schema, message):
    result = {'errors': None, 'data': None}
    try:
        message_data = json.loads(message)
    except JSONDecodeError:
        result.update({'errors': ['Requires valid JSON']})
        return result
    else:
        result['data'] = message_data.get('data', message_data)

    result['errors'] = schema().validate(message_data)
    return result


async def receive_bus_coordinates(request):
    ws = await request.accept()

    while True:
        try:
            received_message = await ws.get_message()
            bus_info = validate(BusSchema, received_message)

            logger.debug(f'Result of validate: {bus_info}')

            errors = bus_info.get('errors')
            if errors:
                response_msg = {'msgType': 'Errors', 'errors': errors}
                await ws.send_message(
                    json.dumps(response_msg, ensure_ascii=False)
                )
            else:
                bus = Bus(**bus_info.get('data'))
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
            if buses_location:
                await ws.send_message(
                    json.dumps(browser_msg, ensure_ascii=True)
                )

                logger.debug(f'Talk to browser:{browser_msg["buses"]}')
                logger.debug(f'{len(buses_location)} buses inside bounds')

            await trio.sleep(1)

        except ConnectionClosed:
            break


async def listen_browser(ws, bounds):
    while True:
        try:
            message = await ws.get_message()

            logger.debug(f'Message from client:{message}')
            message_data = validate(WindowBoundSchema, message)

            logger.debug(f'Result of validate: {message_data}')

            errors = message_data.get('errors')

            if errors:
                response_msg = {'msgType': 'Errors', 'errors': errors}
                await ws.send_message(
                    json.dumps(response_msg, ensure_ascii=False)
                )
            else:
                bounds.update(**message_data.get('data'))
        except ConnectionClosed:
            break


async def talk_to_browser(request):
    ws = await request.accept()
    bounds = WindowBounds()

    # The mutable argument "bounds" is used here
    # (changes in the "listen_browser" function)

    async with trio.open_nursery() as nursery:
        nursery.start_soon(send_buses, ws, bounds)
        nursery.start_soon(listen_browser, ws, bounds)


@click.command()
@click.option(
    "--host",
    "-h",
    default="127.0.0.1",
    help="Address of the main server."
)
@click.option(
    "--bus_server",
    "-bs",
    default="127.0.0.1",
    help="Address of the tracking server."
)
@click.option(
    "--client_port",
    "-cp",
    default=8000,
    help="Client port (ex. browser)."
)
@click.option(
    "--bus_port",
    "-bp",
    default=8080,
    help="Port of the tracking server (GPS gateway)."
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Enabling verbose logging."
)
async def main(host, client_port, bus_server, bus_port, verbose):
    logging.getLogger('trio-websocket').setLevel(logging.WARNING)
    logging.basicConfig(format='%(levelname)s:%(name)s:%(message)s')

    if verbose:
        logger.setLevel(logging.DEBUG)

    async with trio.open_nursery() as nursery:
        nursery.start_soon(
            serve_websocket,
            receive_bus_coordinates,
            bus_server,
            bus_port,
            None
        )
        nursery.start_soon(
            serve_websocket,
            talk_to_browser,
            host,
            client_port,
            None
        )


if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        main(_anyio_backend="trio")
