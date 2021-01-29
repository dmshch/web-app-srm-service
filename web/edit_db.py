# Copyright © 2020 Dmitrii Shcherbakov. All rights reserved.

from pathlib import *
import sqlite3
from servmoncode import db

#edit db from web gui

def select_receiver_for_edit(ip, port):
    with db.DB() as curs:
        # check duplicate by ip and port
        curs.execute('SELECT * FROM receivers WHERE ip=:ip AND port=:port',{"ip":ip, "port":port})
        # only one line is expected because IP and port are unique
        row_of_receivers = curs.fetchall()
        tuple_of_keys = ('ip', 'model', 'satellite', 'login', 'password', 'port', 'state')
        # receiver is dict -> keys: ip, model, satellite, login, password, port, state
        for res in row_of_receivers:
            receiver = dict(zip(tuple_of_keys, res))
    return receiver

def update_receiver(ip, model, satellite, login, password, port, state):
    if state == "used":
        state = 1
    elif state == "don't used":
        state = 0
    with db.DB() as curs:
        # check duplicate by ip and port
        curs.execute('UPDATE receivers SET model=:model, satellite=:satellite, login=:login, password=:password, state=:state WHERE ip=:ip AND port=:port',{"ip":ip, "port":port,"model":model,"satellite":satellite,"login":login,"password":password,"state":state})
    status = "Receiver ip:" + ip + " with port:" + port  + " has been updated."
    return status
