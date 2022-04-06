# Class for satellites

from sqlalchemy import Column, String
from . database import Base

class Satellite(Base):
   __tablename__ = 'satellites'
   guid = Column(String(250), nullable=False, primary_key = True)
   name = Column(String(250), nullable=False)

   def __repr__(self):
      return "name: " + self.name
