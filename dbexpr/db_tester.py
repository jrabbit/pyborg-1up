from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Word(Base):
    __tablename__ = "word"
    id = Column(Integer, primary_key=True)
    word = Column(String)
#    entries = relationship("Entry", back_populates="word")

    def __repr__(self):
        return f"word> {self.word} id> {self.id}"


class Entry(Base):
    __tablename__ = "entry_thru"
    id = Column(Integer, primary_key=True)
    index = Column(Integer)
    line_id = Column(Integer, ForeignKey("line.id"))
    line = relationship("Line")

    def __repr__(self):
        return f"entry> id>{self.id}"


class Line(Base):
    __tablename__ = "line"
    id = Column(Integer, primary_key=True)
    entry = Column(String)
    magic = Column(Integer)
    # there's extra data in the db a integer


class PybMeta(Base):
    __tablename__ = "settings"
    version = Column(String, primary_key=True)


if __name__ == "__main__":
    engine = create_engine("postgresql://pyborg:trustno1@db/pyborg")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    sess = Session()
    sess.add(PybMeta(version="__EXPERIMENTAL__"))
    sess.commit()
