import functools
import itertools
import json
import logging
import os
import random
from contextlib import suppress

import trio
import asyncclick as click
from trio_websocket import ConnectionClosed
from trio_websocket import HandshakeError
from trio_websocket import open_websocket_url


logger = logging.getLogger('fake-bus-service')


def load_routes(directory_path='routes', routes_number=None):
    for filename in os.listdir(directory_path)[:routes_number]:
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)


def relaunch_on_disconnect(async_function):

    @functools.wraps(async_function)
    async def wrapper(*args, **kwargs):

        while True:
            try:
                await async_function(*args, **kwargs)

            except (HandshakeError, ConnectionClosed):
                reconnect_timeout = 5
                logger.debug(
                    f'Disconnect. Try to reconnect in {reconnect_timeout} sec.'
                )
                await trio.sleep(reconnect_timeout)

    return wrapper


async def run_bus(send_channel, bus_id, route, timeout):
    coords = route['coordinates']
    offset = random.randrange(len(coords))
    route_offset = itertools.chain(coords[offset:], coords[:offset])
    route_loop = itertools.cycle(route_offset)

    while True:
        bus_coords = next(route_loop)
        lat, lng = bus_coords[0], bus_coords[1]
        coordinates = {
            'busId': bus_id,
            'lat': lat,
            'lng': lng,
            'route': route['name']
        }
        message = json.dumps(coordinates, ensure_ascii=True)
        await send_channel.send(message)
        logger.debug(f'Sent message: {coordinates}')
        await trio.sleep(timeout)


@relaunch_on_disconnect
async def send_updates(server_address, receive_channel, timeout):
    async with open_websocket_url(server_address) as ws:
        async for value in receive_channel:
            await ws.send_message(value)
            await trio.sleep(timeout)


async def make_channels(nursery, server_addr, sockets_count, timeout):
    send_channels = []
    for _ in range(sockets_count):
        send_channel, receive_channel = trio.open_memory_channel(0)
        nursery.start_soon(
            send_updates, server_addr, receive_channel.clone(), timeout
        )
        send_channels.append(send_channel.clone())
    return send_channels


@click.command()
@click.option(
    "--server",
    "-s",
    default="127.0.0.1",
    help="Address of the tracking server."
)
@click.option(
    "--bus_port",
    "-bp",
    default="8080",
    help="Port of the tracking server."
)
@click.option(
    "--routes_number",
    "-r", default=10,
    help="Number of routes."
)
@click.option(
    "--buses_per_route",
    "-b",
    default=10,
    help="Number of buses per one route."
)
@click.option(
    "--websockets_number",
    "-ws", default=5,
    help="Number of open ws connections."
)
@click.option(
    "--emulator_id",
    "-ei",
    default=1,
    help="Emulator ID.")
@click.option(
    "--refresh_timeout",
    "-to",
    default=1.0,
    help="Timeout for refresh in secs."
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Enabling verbose logging."
)
async def main(
    server, bus_port, routes_number, buses_per_route, websockets_number,
    emulator_id, refresh_timeout, verbose
):

    logging.getLogger('trio-websocket').setLevel(logging.WARNING)
    logging.basicConfig(format='%(message)s')

    if verbose:
        logger.setLevel(logging.DEBUG)

    server_url = f'ws://{server}:{bus_port}'

    async with trio.open_nursery() as nursery:
        send_channels = await make_channels(
            nursery, server_url, websockets_number, refresh_timeout
        )

        for route in load_routes(routes_number=routes_number):
            for bus_index in range(buses_per_route):
                send_channel = random.choice(send_channels)
                bus_id = f'{route["name"]}-{bus_index}'
                nursery.start_soon(
                    run_bus, send_channel, bus_id, route, refresh_timeout
                )


if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        main(_anyio_backend="trio")
