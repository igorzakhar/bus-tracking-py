import itertools
import json
import logging
import os
import random
import sys

import trio
from trio_websocket import open_websocket_url


def load_routes(directory_path='routes'):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)


async def run_bus(send_channel, bus_id, route):
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
        logging.debug(f'Sent message: {coordinates}')
        await trio.sleep(1)


async def send_updates(server_address, receive_channel):
    async with open_websocket_url(server_address) as ws:
        async with receive_channel:
            async for value in receive_channel:
                await ws.send_message(value)
                await trio.sleep(0.1)


async def make_channels(nursery, server_addr, sockets_count):
    send_channels = []
    for _ in range(sockets_count):
        send_channel, receive_channel = trio.open_memory_channel(0)
        async with send_channel, receive_channel:
            nursery.start_soon(
                send_updates, server_addr, receive_channel.clone()
            )
            send_channels.append(send_channel.clone())
    return send_channels


async def main():
    logging.getLogger('trio-websocket').setLevel(logging.WARNING)
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')

    server_url = 'ws://127.0.0.1:8080'
    buses_per_route = 10
    sockets_count = 5

    async with trio.open_nursery() as nursery:
        send_channels = await make_channels(nursery, server_url, sockets_count)

        for route in load_routes():
            for bus_index in range(buses_per_route):
                send_channel = random.choice(send_channels)
                bus_id = f'{route["name"]}-{bus_index}'
                nursery.start_soon(run_bus, send_channel, bus_id, route)


if __name__ == '__main__':
    try:
        trio.run(main)
    except (KeyboardInterrupt, trio.MultiError):
        sys.exit()
