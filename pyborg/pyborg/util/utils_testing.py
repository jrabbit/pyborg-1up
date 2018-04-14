import asyncio


async def do_nothing(channel, msg):
    await asyncio.sleep(1)
    return True
