# Copyright © 2020 Dmitrii Shcherbakov. All rights reserved.

import sqlite3
from pathlib import *
import ipaddress
from servmoncode import db

# add data in sqlite

def add_data(ip, model, satellite, login, password, port, state):
    status = ""

    '''##############################################################'''
    # temp     
    if model == "proview7100mnew" or model == "proview8130":
        return "This model of receivers not supported yet"
    '''##############################################################'''

    if state == "used":
        state = 1
    elif state == "don't used":
        state = 0
    try:
        ipaddress.ip_address(ip)
    except:
        return "Invalid IP address"
    
    with db.DB() as curs:
        # check duplicate by ip and port
        curs.execute('SELECT * FROM receivers WHERE ip=:ip AND port=:port', {"ip":ip, "port":port})
        rows = curs.fetchall()
        # add or return error
        if len(rows) > 0:
            status = "IP address and port exist"
        else:
            ins = 'INSERT INTO receivers (ip, model, satellite, login, password, port, state) VALUES(?, ?, ?, ?, ?, ?, ?)'
        
            # check type and set login and password

            curs.execute(ins, (ip, model, satellite, login, password, port, state))
            status = "IP address and port have been added"
    return status
