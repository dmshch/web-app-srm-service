# Class for type of receivers

from sqlalchemy import Column, String
from . database import Base

class ReceiverType(Base):
   __tablename__ = 'receiver_models'
   guid = Column(String(250), nullable=False, primary_key = True)
   model = Column(String(250), nullable=False)
   login = Column(String(250), nullable=False)
   password = Column(String(250), nullable=False)

   def __repr__(self):
      return "model: " + self.model
