# Copyright © 2020 Dmitrii Shcherbakov. All rights reserved.

import sqlalchemy as sa
import ipaddress
import json
import uuid

keys = ('guid', 'ip', 'port', 'model', 'satellite', 'login', 'password', 'state', 'time', 'c_n', 'eb_no', 'l_m')

class DB():
    engine = None
    def __init__(self):
        try:
            with open("web/settings.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print("Failed to load settings. Check the correctness of the settings file 'web/settings.json'.")
        path = data["dialect"] + "+" + data["driver"] + "://" + data["user"] + ":" + data["password"] + "@" + data["host"] + ":" + data["port"] + "/" + data["dbname"]
        self.engine = sa.create_engine(path)

    def check_value(self, d, c_n_boundary, eb_no_boundary):
        if d["c_n"]  == "not initialized" or d['eb_no'] == "not initialized":
            d["alarm"] = "alarm_medium"
        elif d["c_n"]  == "new" or d['eb_no'] == "new":
            d["alarm"] = "alarm_low"
        elif d["c_n"] == "0" or d['eb_no'] == "0":
            d["alarm"] = "alarm_critical"
            # need try
        elif float(d["c_n"]) <= float(c_n_boundary) or float(d["eb_no"]) <= float(eb_no_boundary):
            d["alarm"] = "alarm_high"
        else:
            d["alarm"] = "alarm_normal"
        return d

    def get_receivers(self, satellite = None, state = None):

        with self.engine.connect() as conn:

            metadata = sa.MetaData()
            receivers = sa.Table('receivers', metadata, autoload=True, autoload_with=conn)

            dict_settings = self.get_settings()
            c_n_boundary, eb_no_boundary = dict_settings["c_n_boundary"], dict_settings["eb_no_boundary"]

            list_of_data = []

            if satellite is None and state is not None:
                query = sa.select([receivers]).where(receivers.columns.state == state)
                ResultProxy = conn.execute(query)
                ResultSet = ResultProxy.fetchall()

            if satellite is None and state is None:
                query = sa.select([receivers])
                ResultProxy = conn.execute(query)
                ResultSet = ResultProxy.fetchall()
                # ? ? ?
                for row in ResultSet:
                    d = dict(zip(keys, row))
                    list_of_data.append(d)
                self.engine.dispose()
                return list_of_data

            if satellite is not None and state is not None:
                query = sa.select([receivers]).where(receivers.columns.satellite == satellite)
                query = query.where(receivers.columns.state == "True")
                ResultProxy = conn.execute(query)
                ResultSet = ResultProxy.fetchall()

            for row in ResultSet:
                d = dict(zip(keys, row))
                d = self.check_value(d, c_n_boundary, eb_no_boundary)
                list_of_data.append(d)
            sortBySat = lambda list_of_data: list_of_data["satellite"]
            list_of_data.sort(key = sortBySat)
            self.engine.dispose()
            return list_of_data
            
    def get_settings(self):
        with self.engine.connect() as conn:
            metadata = sa.MetaData()
            settings = sa.Table('settings', metadata, autoload=True, autoload_with=conn)
            query = sa.select([settings])
            ResultProxy = conn.execute(query)
            ResultSet = ResultProxy.fetchall()
            dict_settings = dict()
            for row in ResultSet:
                dict_settings[row[0]] = row[1]
            self.engine.dispose()
            return dict_settings

    def set_settings(self, settings_dict):
        status = ()
        with self.engine.connect() as conn:
            for key in settings_dict:
                if settings_dict[key] != "":
                    if key == "c_n_boundary" or key == "eb_no_boundary":
                        try:
                            float(settings_dict[key])
                        except:
                            status = ("An error occurred while updating the " + key + ". Please check input value. ", False)
                            continue
                    try:
                        metadata = sa.MetaData()
                        settings = sa.Table('settings', metadata, autoload = True, autoload_with = conn)
                        query = sa.update(settings).values(value = settings_dict[key])
                        query = query.where(settings.columns.name == key)
                        ResultProxy = conn.execute(query)
                        status = (key + " has been updated. ", True)
                    except:
                        status = ("An error occurred while updating the settings.", False)
        self.engine.dispose()
        return (status, )

    def get_satellites(self):
        with self.engine.connect() as conn:
            metadata = sa.MetaData()
            satellites = sa.Table('satellites', metadata, autoload=True, autoload_with=conn)
            query = sa.select([satellites])
            ResultProxy = conn.execute(query)
            ResultSet = ResultProxy.fetchall()
            dict_satellites = dict()
            for row in ResultSet:
                dict_satellites[row[0]] = row[1]
            self.engine.dispose()
            return dict_satellites            

    # IN PROGRESS
    def add_satellites(self, satellite):
        satellite = satellite.strip()
        status = ()
        with self.engine.connect() as conn:
            metadata = sa.MetaData()
            satellites = sa.Table('satellites', metadata, autoload=True, autoload_with=conn)
            try:
                if satellites != "":
                    query = sa.select([satellites]).where(satellites.columns.name == satellite)
                    ResultProxy = conn.execute(query)
                    ResultSet = ResultProxy.fetchall()
                    if len(ResultSet) == 0:
                        guid = str(uuid.uuid4())
                        query = sa.insert(satellites).values(guid = guid, name = satellite)
                        ResultProxy = conn.execute(query)
                        status = ("Satellite has been added", True)
                    else:
                        status =  ("Satellite exists.", False)
            except:
                status = ("An error occurred while adding the receiver.", False)
        self.engine.dispose()
        return (status, )
    
    def get_receiver_authentication(self):
        with self.engine.connect() as conn:
            metadata = sa.MetaData()
            receiver_models = sa.Table('receiver_models', metadata, autoload = True, autoload_with = conn)
            query = sa.select([receiver_models])
            ResultProxy = conn.execute(query)
            ResultSet = ResultProxy.fetchall()
            dict_receiver_models = dict()
            for row in ResultSet:
                dict_receiver_models[row[1]] = [row[2],row[3]]
            self.engine.dispose()
            return dict_receiver_models

    def set_receiver_authentication(self, receiver, login = "", password = ""):
        s1, s2, s3 = (), (), ()
        if receiver == None:
            return "You must choose the type of receiver."
        if login != "" or password != "":
            with self.engine.connect() as conn:
                metadata = sa.MetaData()
                receiver_models = sa.Table('receiver_models', metadata, autoload = True, autoload_with = conn)
                try:
                    if login != "" and  password != "":
                        query = sa.update(receiver_models).values(login = login, password = password)
                        query = query.where(receiver_models.columns.model == receiver)
                        ResultProxy = conn.execute(query)                        
                        s1 = ("The login and password have been updated.", True)
                except:
                    s1 = ("An error occurred while updating the login and the password.", False)
                try:
                    if login != "" and password == "":
                        query = sa.update(receiver_models).values(login = login)
                        query = query.where(receiver_models.columns.model == receiver)
                        ResultProxy = conn.execute(query)
                        s2 = ("The login has been updated.", True)
                except:
                    s2 = ("An error occurred while updating the login.", False)
                try:
                    if login == "" and password != "":
                        query = sa.update(receiver_models).values(password = password)
                        query = query.where(receiver_models.columns.model == receiver)
                        ResultProxy = conn.execute(query)
                        s3 = ("The password has been updated.", True)
                except:
                    s3 = ("An error occurred while updating the password.", False)
        self.engine.dispose()
        return (s1, s2, s3)

    def get_user_authentication(self):
        with self.engine.connect() as conn:
            metadata = sa.MetaData()
            users = sa.Table('users', metadata, autoload=True, autoload_with=conn)
            query = sa.select([users])
            ResultProxy = conn.execute(query)
            ResultSet = ResultProxy.fetchall()
            dict_users = dict()
            for row in ResultSet:
                dict_users[row[0]] = row[1]
            self.engine.dispose()
            return dict_users

    def set_user_authentication(self, user, password):
        s1, s2, s3 = (), (), ()
        if user != None and password != "":
            with self.engine.connect() as conn:
                try:
                    metadata = sa.MetaData()
                    users = sa.Table('users', metadata, autoload = True, autoload_with = conn)
                    query = sa.update(users).values(password = password)
                    query = query.where(users.columns.login == user)
                    ResultProxy = conn.execute(query)
                except:
                    s1 = ("An error occurred while updating the password.", False)
        if user == None:
            s2 = ("An error occurred while updating the password: you must choose the username. ", False)
        if passwd == "":
            s3 = ("An error occurred while updating the password: you must enter the password. ", False)
        self.engine.dispose()
        return (s1, s2, s3)

    def add_receiver(self, ip, model, satellite, login, password, port, state):
        if state == "used":
            state = True
        if state == "don't used":
            state = False
        try:
            ipaddress.ip_address(ip)
        except:
            self.engine.dispose()
            return "Invalid IP address."

        # check login and password
        with self.engine.connect() as conn:
            metadata = sa.MetaData()
            receivers = sa.Table('receivers', metadata, autoload = True, autoload_with = conn)
            try:
                query = sa.select([receivers]).where(receivers.columns.ip == ip)
                query = query.where(receivers.columns.port == port)
                ResultProxy = conn.execute(query)
                ResultSet = ResultProxy.fetchall()
                if len(ResultSet) == 0:
                    guid = str(uuid.uuid4())
                    not_init = "new"
                    # guid | ip | port | model | satellite | login | password | state |  c_n | eb_no | l_m | time
                    query = sa.insert(receivers).values(guid = guid, ip = ip, port = port, model = model, satellite = satellite, login = login, password = password, state = state, c_n = not_init, eb_no = not_init, l_m = not_init, time = not_init)
                    ResultProxy = conn.execute(query)
                    status = ("Receiver has been added.", True)
                else:
                    status =  ("IP and port exists.", False)
            except:
                status = ("An error occurred while adding the receiver.", False)
        self.engine.dispose()
        return status

    def delete_receiver(self, ip, port):
        with self.engine.connect() as conn:
            metadata = sa.MetaData()
            receivers = sa.Table('receivers', metadata, autoload = True, autoload_with = conn)
            try:
                query = sa.delete(receivers)
                query = query.where(receivers.columns.ip == ip)
                query = query.where(receivers.columns.port == port)
                ResultProxy = conn.execute(query)
                status = ("Receiver has been deleted", True)
            except:
                status = ("An error occurred while deleting the receiver.",False)
        self.engine.dispose()
        return status

    def get_receiver(self, ip, port):
        status = ""
        d = dict()
        dict_settings = self.get_settings()
        c_n_boundary, eb_no_boundary = dict_settings["c_n_boundary"], dict_settings["eb_no_boundary"]
        with self.engine.connect() as conn:
            try:
                metadata = sa.MetaData()
                receivers = sa.Table('receivers', metadata, autoload = True, autoload_with = conn)
                query = sa.select([receivers]).where(receivers.columns.ip == ip)
                query = query.where(receivers.columns.port == port)
                ResultProxy = conn.execute(query)
                ResultSet = ResultProxy.fetchall()                
                for row in ResultSet:
                    d = dict(zip(keys, row))
                    d = self.check_value(d, c_n_boundary, eb_no_boundary)
                status = ("", True)
            except:
                status = ("An error occurred while getting the data from DB.", False)
        self.engine.dispose()
        return (status, d)

    def update_receiver(self, ip, model, satellite, login, password, port, state):
        if state == "used":
            state = True
        if state == "don't used":
            state = False
        s1, s2, s3, s4 = (), (), (), ()
        with self.engine.connect() as conn:
            metadata = sa.MetaData()
            receivers = sa.Table('receivers', metadata, autoload = True, autoload_with = conn)
            try:
                if login != "" and password != "":
                    query = sa.update(receivers).values(login = login, password = password)
                    query = query.where(receivers.columns.ip == ip)
                    query = query.where(receivers.columns.port == port)
                    ResultProxy = conn.execute(query)
                    s1 = ("The login/password have been updated. ", True)
            except:
                s1 = ("An error occurred while updating the receiver (login/password)", False)
            try:
                if login != "" and password == "":
                    query = sa.update(receivers).values(login = login)
                    query = query.where(receivers.columns.ip == ip)
                    query = query.where(receivers.columns.port == port)
                    ResultProxy = conn.execute(query)
                    s2 = ("The login has been updated.", True)
            except:
                s2 = ("An error occurred while updating the receiver (login). ", False)
            try:
                if login == "" and password != "":
                    query = sa.update(receivers).values(password = password)
                    query = query.where(receivers.columns.ip == ip)
                    query = query.where(receivers.columns.port == port)
                    ResultProxy = conn.execute(query)
                    s3 = ("The password has been updated.", True)
            except:
                s3 = ("An error occurred while updating the receiver (password). ", False)
            try:
                query = sa.update(receivers).values(model = model, satellite = satellite, state = state)
                query = query.where(receivers.columns.ip == ip)
                query = query.where(receivers.columns.port == port)
                ResultProxy = conn.execute(query)
                s4 = ("The model/satellite/state have been updated. ", True)
            except:
                s4 = ("An error occurred while updating the model/satellite/state. ", False)
        self.engine.dispose()
        return (s1, s2, s3, s4)
