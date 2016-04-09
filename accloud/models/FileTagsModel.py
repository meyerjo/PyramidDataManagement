from sqlalchemy import Integer
from sqlalchemy import Column, String, DateTime

import datetime

from models import Base


class FileTagsModel(Base):

    __tablename__ = 'filetags'

    id = Column(Integer, primary_key=True)
    file = Column(String, nullable=False)
    tags = Column(String, nullable=False)  # TODO: make sure that this is easily searchable later on
    creationtime = Column(DateTime, nullable=False, default=datetime.datetime.now())

    def __init__(self, file, tags):
        self.file = file
        self.tags = tags