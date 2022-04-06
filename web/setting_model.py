# Class for settings

from sqlalchemy import Column, String
from . database import Base

class Setting(Base):
   __tablename__ = 'settings'
   name = Column(String(250), nullable=False, primary_key = True)
   value = Column(String(250), nullable=False)

   def __repr__(self):
      return "name: " + self.name + "; value: " + self.value
