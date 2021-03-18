# Copyright © 2020 Dmitrii Shcherbakov. All rights reserved.

import sqlalchemy as sa
import ipaddress

dialect = "postgresql"
driver = "psycopg2"
user = "postgres"
password = "docker"
host = "127.0.0.1"
port = "5432"
dbname = "servermon"

keys = ('ip', 'model', 'satellite', 'login', 'password', 'port', 'state', 'time', 'c_n', 'eb_no', 'l_m')

class DB:

    def __init__(self):
        self.path = dialect + "+" + driver + "://" + user+ ":" + password + "@" + host + ":" + port + "/" + dbname
        #print(self.path)

    def __enter__(self):
        self.conn = sa.create_engine(self.path)
        return self.conn

    def __exit__(self, *args):
        # ?
        pass

def get_data_receivers(satellite = None, state = None):
    with DB() as conn:
        dict_settings = get_settings()
        c_n_boundary, eb_no_boundary = dict_settings["c_n_boundary"], dict_settings["eb_no_boundary"]
        
        list_of_data = []
        if satellite is None and state is not None:
            postgresql_select_query = 'SELECT * FROM receivers WHERE state= %s'
            rows = conn.execute(postgresql_select_query, (state, ))

        if satellite is None and state is None:
             postgresql_select_query = 'SELECT * FROM receivers'
             rows = conn.execute(postgresql_select_query)
             # ? ? ?
             for row in rows:
                 d = dict(zip(keys, row))
                 list_of_data.append(d)
             return list_of_data

        if satellite is not None and state is not None:
             postgresql_select_query = 'SELECT * FROM receivers WHERE state= %s AND satellite= %s'
             rows = conn.execute(postgresql_select_query, (state, satellite , ))

        for row in rows:
            d = dict(zip(keys, row))
            #print(d["c_n"], d['eb_no'])
            if d["c_n"]  == "not initialized" or d['eb_no'] == "not initialized":
                d["color"] = "gray"
            elif d["c_n"] == "0" or d['eb_no'] == "0":
                d["color"] = "red"
            # need try
            elif float(d["c_n"]) <= float(c_n_boundary) or float(d["eb_no"]) <= float(eb_no_boundary):
                d["color"] = "yellow"
            else:
                d["color"] = "green"
            
            list_of_data.append(d)
    return list_of_data

def get_settings():
    with DB() as conn:
        # get settings - boundary for c_n and eb_no; c_n_boundary = 8.0, eb_no_boundary = 6.0
        postgresql_select_query = 'SELECT * FROM settings'
        rows = conn.execute(postgresql_select_query)
        dict_settings = dict()
        for row in rows:
            dict_settings[row[0]] = row[1]
        return dict_settings

def set_settings(time = None, c_n = None, eb_no = None):
    s1, s2 = "", ""
    with DB() as conn:
        if c_n != "":
            try:
                c_n = float(c_n)
                postgresql_select_query = "UPDATE settings SET value = %s WHERE name = 'c_n_boundary'"
                rows = conn.execute(postgresql_select_query, (c_n, ))
                s1 = "C/N has been updated. "
            except:
                s1 = "An error occurred while updating the C/N. "
        if eb_no != "":
            try:
                eb_no = float(eb_no)
                postgresql_select_query = "UPDATE settings SET value = %s WHERE name = 'eb_no_boundary'"
                rows = conn.execute(postgresql_select_query, (eb_no, ))
                s2 = "Eb/NO has been updated"
            except:
                s2 = "An error occurred while updating the Eb/NO. "
    return s1 + s2

def get_receiver_authentication():
    with DB() as conn:
        postgresql_select_query = 'SELECT * FROM receiver_authentication'
        rows = conn.execute(postgresql_select_query)
        dict_settings = dict()
        for row in rows:
            dict_settings[row[0]] = [row[1],row[2]]
        return dict_settings

def set_receiver_authentication(receiver, login = "", password = ""):
    s1, s2, s3 = "", "", ""
    if receiver == None:
        return "You must choose the type of receiver."
    if login != "" or password != "":
        with DB() as conn:
            try:
                if login != "" and  password != "":
                    postgresql_select_query = "UPDATE receiver_authentication SET login = %s, password = %s WHERE model = %s"
                    rows = conn.execute(postgresql_select_query, (login, password, receiver, ))
                    s1 = "The login and password have been updated."
            except:
                s1 = "An error occurred while updating the login and the password."
            try:
                if login != "" and password == "":
                    postgresql_select_query = "UPDATE receiver_authentication SET login = %s WHERE model = %s"
                    rows = conn.execute(postgresql_select_query, (login, receiver, ))
                    s2 = "The login has been updated."
            except:
                s2 = "An error occurred while updating the login."
            try:
                if login == "" and password != "":
                    postgresql_select_query = "UPDATE receiver_authentication SET password = %s WHERE model = %s"
                    rows = conn.execute(postgresql_select_query, (password, receiver, ))
                    s3 = "The password has been updated."
            except:
                s3 = "An error occurred while updating the password."
    return s1 + s2 + s3

def get_user_authentication():
    with DB() as conn:
        postgresql_select_query = 'SELECT * FROM user_authentication'
        rows = conn.execute(postgresql_select_query)
        dict_settings = dict()
        for row in rows:
            dict_settings[row[0]] = row[1]
        return dict_settings

def set_user_authentication(user, password):
    status, s1, s2 = "", "", ""
    if user != None and password != "":
        with DB() as conn:
            try:
                postgresql_select_query = "UPDATE user_authentication SET password = %s WHERE login = %s"
                rows = conn.execute(postgresql_select_query, (password, user, ))
                status = "The password has been updated. "
            except:
                status = "An error occurred while updating the password."
    if user == None:
        s1 = "An error occurred while updating the password: you must choose the username. "
    if password == "":
        s2 = "An error occurred while updating the password: you must enter the password. "
    return status + s1 + s2

def add(ip, model, satellite, login, password, port, state):
    if state == "used":
        state = True
    if state == "don't used":
        state = False
    try:
        ipaddress.ip_address(ip)
    except:
        return "Invalid IP address."

    # check login and password

    with DB() as conn:
        try:
            if login == "" and password == "":
                postgresql_select_query = 'SELECT COUNT(*) FROM receivers WHERE ip= %s AND port= %s'
                #it returns like [(0,)] or [(1,)]
                if ([i for i in conn.execute(postgresql_select_query, (ip, port, ))][0][0]) == 0:
                    not_init = "not initialized"
                    postgresql_select_query = 'INSERT INTO receivers (ip, model, satellite, port, state, c_n, eb_no, l_m, time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
                    rows = conn.execute(postgresql_select_query, (ip, model, satellite, port, state, not_init, not_init, not_init, not_init ))
                    status = "Receiver has been added"
                else:
                    status =  "IP and port exists."
        except:
            status = "An error occurred while adding the receiver."
    print(ip, model, satellite, login, password, port, state)
    return status

def delete(ip, port):
    with DB() as conn:
        try:
            postgresql_select_query = 'DELETE FROM receivers WHERE ip = %s AND port = %s'
            rows = conn.execute(postgresql_select_query, (ip, port))
            status = "Receiver has been deleted"
        except:
            status = "An error occurred while deleting the receiver."
    return status

def get(ip, port):
    status = ""
    d = dict()
    with DB() as conn:
        try:
            postgresql_select_query = 'SELECT * FROM receivers WHERE ip = %s AND port = %s'
            rows = conn.execute(postgresql_select_query, (ip, port))
            for row in rows:
                 d = dict(zip(keys, row))
        except:
            status = "An error occurred while getting the data from DB."
    return (status, d)

def update(ip, model, satellite, login, password, port, state):
    print(ip, model, satellite, login, password, port, state)
    if state == "used":
        state = True
    if state == "don't used":
        state = False
    s1, s2, s3, s4 = "", "", "", ""
    with DB() as conn:
        try:
            if login != "" and password != "":
                postgresql_select_query = "UPDATE receivers SET login = %s, password = %s WHERE ip = %s AND port = %s"
                rows = conn.execute(postgresql_select_query, (login, password, ip, port, ))
                s1 = "The login and password have been updated. "
        except:
            s1 = "An error occurred while updating the receiver (login and password)"
        try:
            if login != "" and password == "":
                postgresql_select_query = "UPDATE receivers SET login = %s WHERE ip = %s AND port = %s"
                rows = conn.execute(postgresql_select_query, (login, ip, port, ))
                s2 = "The login has been updated."
        except:
            s2 = "An error occurred while updating the receiver (login). "
        try:
            if login == "" and password != "":
                postgresql_select_query = "UPDATE receivers SET password = %s WHERE ip = %s AND port = %s"
                rows = conn.execute(postgresql_select_query, (password, ip, port, ))
                s3 = "The password has been updated."
        except:
            s3 = "An error occurred while updating the receiver (password). "
        try:
            postgresql_select_query = "UPDATE receivers SET model = %s, satellite = %s, state = %s WHERE ip = %s AND port = %s"
            rows = conn.execute(postgresql_select_query, (model, satellite, state, ip, port, ))
            s4 = "The model, satellite and state have been updated. "
        except:
            s4 = "An error occurred while updating the model, satellite and state. "
    return s1 + s2 + s3 + s4
