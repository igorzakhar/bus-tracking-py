import json
import logging

from contextlib import suppress

import asyncclick as click

from trio_websocket import open_websocket_url


HARMFULL_MESSAGES = [
    'Test message',
    json.dumps({'msgType': 'ErrorMsgType'}),
    json.dumps({'msgType': 'newBounds', "data": {'lat': 20, 'lng': 30}}),
    json.dumps(
        {
            'msgType': 'newBounds',
            "data":
                {
                    'south_lat': 'A',
                    'east_lng': 2.0,
                    'west_lng': 3.0,
                    'north_lat': 4.0
                }
        }
    )
]


async def send_harmfull_message(ws, message):
    await ws.send_message(message)
    resp = await ws.get_message()
    logging.debug(json.loads(resp))


@ click.command()
@ click.option(
    "--server",
    "-s",
    default="127.0.0.1",
    help="Address of the tracking server."
)
@ click.option(
    "--port",
    "-p",
    default="8000",
    help="Port of the tracking server."
)
async def main(server, port):
    logging.getLogger('trio-websocket').setLevel(logging.WARNING)
    logging.basicConfig(
        level=logging.DEBUG,
        format='Response:%(message)s'
    )

    server_url = f'ws://{server}:{port}'

    async with open_websocket_url(server_url) as ws:
        for msg in HARMFULL_MESSAGES:
            await send_harmfull_message(ws, msg)


if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        main(_anyio_backend="trio")
