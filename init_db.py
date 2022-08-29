# Copyright © 2022 Dmitrii Shcherbakov. All rights reserved.

from web import database
import sqlalchemy as sa
import bcrypt

def init():
    with open('schema.sql', 'r', encoding='utf-8') as schema:
        t = sa.text(schema.read())
    '''
    if bcrypt.checkpw(password, hashed):
        print("It Matches!")
    else:
        print("It Does not Match :(")
    '''
    with database.engine.connect() as conn:
        conn.execute(t)
        metadata = sa.MetaData()
        # for admin
        if user == "admin":
            password = bytes("admin".encode("utf-8"))
            hashed = bcrypt.hashpw(password, bcrypt.gensalt())
            users = sa.Table('users', metadata, autoload=True, autoload_with=conn)
            query = sa.update(users).values(password = hashed.decode("utf-8"))
            query = query.where(users.columns.login == "admin")
            results = conn.execute(query)
        # for monitor
        if user == "monitor":
		    password = bytes("monitor".encode("utf-8"))
            hashed = bcrypt.hashpw(password, bcrypt.gensalt())
            users = sa.Table('users', metadata, autoload=True, autoload_with=conn)
            query = sa.update(users).values(password = hashed.decode("utf-8"))
            query = query.where(users.columns.login == "monitor")
            results = conn.execute(query)
        conn.close()
        database.engine.dispose()
		
if __name__ == "__main__":
    init()
