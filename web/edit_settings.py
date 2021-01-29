# Copyright © 2020 Dmitrii Shcherbakov. All rights reserved.

from pathlib import *
import sqlite3
from servmoncode import db

#edit settings from web gui

# load all settings as dict 
def get_settings():
    settings, receiver_authentication, user_authentication = dict(), dict(),dict()
    
    return settings, receiver_authentication, user_authentication

def get_global_settings():
    values = dict()
    with db.DB() as curs:
        curs.execute('SELECT * FROM settings')
        rows = curs.fetchall()
        for row in rows:
            values[row[0]] = row[1]
    return values

def set_global_settings(time, cn, ebno):
    with db.DB() as curs:
        status = ''
        if time != "":
            # to integer
            try:
                int(time)
                curs.execute('UPDATE settings SET value=:time WHERE name="period"',{"time":time })
            except:
                status += "Invalid value for 'Period of update'"
        if cn != "":
            # to decimal
            try:
                float(cn)
                curs.execute('UPDATE settings SET value=:cn WHERE name="c_n_boundary"',{"cn":cn })
            except:
                status += "Invalid value for 'C/N'"
        if ebno != "":
            # to decimal
            try:
                float(ebno)
                curs.execute('UPDATE settings SET value=:ebno WHERE name="eb_no_boundary"',{"ebno":ebno })
            except:
                status += "Invalid value for 'Eb/NO'"
    return status

def get_users_settings():
    values = dict()
    with db.DB() as curs:
        curs.execute('SELECT * FROM user_authentication')
        rows = curs.fetchall()
        for row in rows:
            values[row[0]] = row[1]
    return values

def set_users_settings(admin_password, monitor_password):
    status = ''
    if admin_password != "":
        pass
    if monitor_password != "":
        pass

def get_receivers_settings():
    with db.DB() as curs:
        values = dict()
        curs.execute('SELECT * FROM receiver_authentication')
        rows = curs.fetchall()
        for row in rows:
            values[row[0]] = (row[1], row[2])
    return values

def set_receivers_settings():
    pass

