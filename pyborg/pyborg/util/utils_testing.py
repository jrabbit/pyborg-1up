import asyncio

async def do_nothing(channel, msg, loop):
    await asyncio.sleep(1, loop=loop)
    return True