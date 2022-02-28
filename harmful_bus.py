import json
import logging

from contextlib import suppress

import asyncclick as click

from trio_websocket import open_websocket_url


HARMFULL_MESSAGES = [
    'Test message',
    json.dumps({'lat': 11, 'lng': 12, 'route': 'abc'}),
    json.dumps({'busId': 123, 'lat': 'ABC', 'lng': 'ABC', 'route': 123}),
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
    default="8080",
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
