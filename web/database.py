# 

import sqlalchemy as sa
#from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json

try:
    with open("web/settings.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print("Failed to load settings. Check the correctness of the settings file 'web/settings.json'.")
    
path = data["dialect"] + "+" + data["driver"] + "://" + data["user"] + ":" + data["password"] + "@" + data["host"] + ":" + data["port"] + "/" + data["dbname"]
    
engine = sa.create_engine(path, pool_size=10, max_overflow=20)

SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)

Base = declarative_base()
