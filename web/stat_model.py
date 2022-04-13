# Class for statistics

from sqlalchemy import Column, String, DateTime
from . database import Base

class Stat(Base):
   __tablename__ = 'statistics'
   ip = Column(String(250), nullable=False)
   port = Column(String(250), nullable=False)
   c_n = Column(String(250), nullable=False) 
   eb_no = Column(String(250), nullable=False)
   l_m = Column(String(250), nullable=False)
   date_time = Column(DateTime(timezone=False), nullable=False)
   guid = Column(String(250), nullable=False, primary_key = True)
   
   def __repr__(self):
      return self.ip + "; " + self.port + "; " + self.c_n + "; " + self.eb_no + "; " + self.l_m + "; "+ str(self.date_time) + "; " + str(self.guid)
