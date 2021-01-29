# Copyright © 2020 Dmitrii Shcherbakov. All rights reserved.

import sqlite3
from pathlib import *
from servmoncode import db

# delete data from sqlite

def delete_data(ip, port):
    status = ""
    with db.DB() as curs:
        curs.execute('DELETE FROM receivers WHERE ip=:ip AND port=:port',{"ip":ip, "port":port})
        status = "IP address and port have been removed"
    return status
