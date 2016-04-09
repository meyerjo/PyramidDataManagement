from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy import Boolean

from models import Base


class FileDescriptionModel(Base):

    __tablename__ = 'filedescription'

    id = Column(Integer, primary_key=True)
    file = Column(String, nullable=False)
    obj = Column(String, nullable=False)
    username = Column(String, nullable=True)
    autosave = Column(Boolean, default=False)

    def __init__(self, file, json, username=None):
        self.file = file
        self.obj = json
        if username is not None:
            self.username = username







