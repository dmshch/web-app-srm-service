# Class for users

from sqlalchemy import Column, String
from . database import Base

class User(Base):
   __tablename__ = 'users'
   login = Column(String(250), nullable=False, primary_key = True)
   password = Column(String(250), nullable=False)

   def __repr__(self):
      return "login: " + self.login + "; password: " + self.password
