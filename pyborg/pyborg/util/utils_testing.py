import asyncio


async def do_nothing(channel, msg): # noqa: unused-argument
    await asyncio.sleep(1)
    return True
