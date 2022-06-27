# Class for users

from sqlalchemy import Column, String, Boolean
from . database import Base

class Receiver(Base):
   __tablename__ = 'receivers'
   guid = Column(String(250), nullable=False, primary_key = True)
   ip = Column(String(250), nullable=False)
   port = Column(String(250), nullable=False)
   model = Column(String(250), nullable=False)
   satellite = Column(String(250), nullable=False)
   login = Column(String(250), nullable=False)
   password = Column(String(250), nullable=False)
   state = Column(Boolean, nullable=False)
   time = Column(String(250), nullable=False)
   c_n = Column(String(250), nullable=False)
   eb_no = Column(String(250), nullable=False)
   l_m = Column(String(250), nullable=False)
   service = Column(String(250), nullable=False)
   cc_delta = Column(String(250), nullable=False)

   def __repr__(self):
      return "ip: " + self.ip + "; port: " + self.port
