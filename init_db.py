# Copyright © 2022 Dmitrii Shcherbakov. All rights reserved.

from web import database
import sqlalchemy as sa
import bcrypt

def first_init_db():
    with open('schema.sql', 'r', encoding='utf-8') as schema:
        t = sa.text(schema.read())
    admin_1, admin_2, monitor_1, monitor_2 = "" , "", "", ""
    while admin_1 == "" or admin_2 == "" or admin_1 != admin_2:
        admin_1 = input("Please type password for user admin:")
        admin_2 = input("Please retype password for user admin:")
        if admin_1 != admin_2:
            print("The entered passwords do not match. Please retype.")
    while monitor_1 == "" or monitor_2 == "" or monitor_1 != monitor_2:
        monitor_1 = input("Please type password for user monitor:")
        monitor_2 = input("Please retype password for user monitor:")
        if monitor_1 != monitor_2:
            print("The entered passwords do not match. Please retype.")
    with database.engine.connect() as conn:
        conn.execute(t)
        metadata = sa.MetaData()
        # for admin
        password = bytes(admin_2.encode("utf-8"))
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())
        users = sa.Table('users', metadata, autoload=True, autoload_with=conn)
        query = sa.update(users).values(password = hashed.decode("utf-8"))
        query = query.where(users.columns.login == "admin")
        results = conn.execute(query)
        # for monitor
        password = bytes(monitor_2.encode("utf-8"))
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())
        users = sa.Table('users', metadata, autoload=True, autoload_with=conn)
        query = sa.update(users).values(password = hashed.decode("utf-8"))
        query = query.where(users.columns.login == "monitor")
        results = conn.execute(query)
        # END
        conn.close()
        database.engine.dispose()
        
if __name__ == "__main__":
    answer = input("Create new tables [type 'y' for create and 'q' for exit]? : ")
    if answer == "y":
        first_init_db()
