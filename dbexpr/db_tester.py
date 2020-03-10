import asyncio
import aiopg
from aiopg.sa import create_engine
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Word(Base):
    __tablename__ = 'word'
    id = Column(Integer, primary_key=True)
    word = Column(String)
    entries = relationship("Entry", back_populates="word")

class Entry(Base):
    __tablename__ = 'entry_thru'
    id = Column(Integer, primary_key=True)
    index = Column(Integer)
    line_id = Column(Integer, ForeignKey('line.id'))
    line = relationship("Line")
class Line(Base):
    __tablename__ = 'line'
    id = Column(Integer, primary_key=True)
    entry = Column(String)
    magic = Column(Integer)
    # there's extra data in the db a integer

class PybMeta(Base):
    __tablename__ = 'settings'
    version = Column(String, primary_key=True)


async def go():
    async with create_engine(user="pyborg", database="pyborg", "host"="db", "password"="0V1!v@aS") as engine
        async with engine.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                ret = []
                async for row in cur:
                    ret.append(row)
                assert ret == [(1,)]
    print("ALL DONE")

loop = asyncio.get_event_loop()
loop.run_until_complete(go())
