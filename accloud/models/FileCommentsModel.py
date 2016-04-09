import datetime

from sqlalchemy import DateTime, Column, Integer, String, Boolean

from models import Base


class FileCommentsModel(Base):

    __tablename__ = 'filecomments'

    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    object = Column(String, nullable=False)
    autosave = Column(Boolean, nullable=False, default=False)

    def __init__(self, filename, json):
        self.filename = filename
        self.object = json
