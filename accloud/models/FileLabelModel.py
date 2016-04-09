import datetime

from sqlalchemy import DateTime, Column, Integer, String, Boolean

from models import Base


class FileLabelModel(Base):

    __tablename__ = 'filelabels'

    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    label = Column(String, nullable=False)
    autosave = Column(Boolean, nullable=False, default=False)
    create = Column(DateTime, default=datetime.datetime.now())

    def __init__(self, filename, label):
        self.filename = filename
        self.label = label
