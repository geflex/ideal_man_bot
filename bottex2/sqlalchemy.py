from typing import Type

from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.orm import sessionmaker


Session = sessionmaker()


# noinspection PyArgumentList
class _Model:
    session = Session()
    __tablename__: str

    @classmethod
    async def get_or_create(cls, **kwargs):
        user = cls.session.query(cls).filter_by(**kwargs).one_or_none()
        if user is None:
            user = cls(**kwargs)
            cls.session.add(user)
            cls.session.commit()
        return user

    async def update(self, **kwargs):
        for field, value in kwargs.items():
            if hasattr(self, field):
                setattr(self, field, value)
            else:
                raise AttributeError(f'There is no column {field} in {self.__tablename__}')
        self.session.commit()

    async def delete(self):
        self.session.delete(self)
        self.session.commit()


Model = declarative_base(cls=_Model)


def set_engine(engine):
    Model.session.bind = engine


def create_tables(engine):
    Model.metadata.create_all(engine)
