import asyncio
import aiopg
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Word(Base):
    __tablename__ = 'words'
    id = Column(Integer, primary_key=True)
    word = Column(String)
    entry = Column(String)

class Line(Base):
    __tablename__ = 'lines'
    id = Column(Integer, primary_key=True)
    entry = Column(String)

dsn = 'dbname=pyborg user=pyborg password=0V1!v@aS host=db'

async def go():
    async with aiopg.create_pool(dsn) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                ret = []
                async for row in cur:
                    ret.append(row)
                assert ret == [(1,)]
    print("ALL DONE")

loop = asyncio.get_event_loop()
loop.run_until_complete(go())
