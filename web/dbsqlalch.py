# Copyright © 2020 Dmitrii Shcherbakov. All rights reserved.

import sqlalchemy as sa
import ipaddress
import json
import uuid
# Statistic
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.dates as mdates
import io
import numpy as np
from datetime import datetime
from datetime import timedelta
# ORM
from .user_model import User
from .setting_model import Setting
from .receiver_model import Receiver
from .satellite_model import Satellite
from .receiver_type_model import ReceiverType
from . import database

session = database.SessionLocal()

keys = ('guid', 'ip', 'port', 'model', 'satellite', 'login', 'password', 'state', 'time', 'c_n', 'eb_no', 'l_m', 'service')

def check_value(d, c_n_boundary, eb_no_boundary):
    if d["c_n"]  == "connection error" or d['eb_no'] == "connection error":
        d["alarm"] = "alarm_medium"
    elif d["c_n"]  == "new" or d['eb_no'] == "new":
        d["alarm"] = "alarm_low"
    elif d["c_n"] == "0" or d['eb_no'] == "0" or d["c_n"] == "parsing error" or d['eb_no'] == "parsing error":
        d["alarm"] = "alarm_critical"
        # need try
    elif float(d["c_n"]) <= float(c_n_boundary) or float(d["eb_no"]) <= float(eb_no_boundary):
        d["alarm"] = "alarm_high"
    else:
        d["alarm"] = "alarm_normal"
    return d

def get_user_authentication():
    users_dict = dict()
    for row in session.query(User, User.login, User.password).all():
        users_dict[row.login] = row.password
    session.close()
    return users_dict

def set_user_authentication(login, password):
    status = ()
    if login != None and password != "":
        user = session.query(User).filter_by(login = login).first()
        user.password = password
        session.commit()
        session.close()
    if login == None:
        status = ("An error occurred while updating the password: you must choose the username. ", False)
    if password == "":
        status = ("An error occurred while updating the password: you must enter the password. ", False)
    return status

def get_settings():
    settings_dict = dict()
    for row in session.query(Setting, Setting.name, Setting.value).all():
        settings_dict[row.name] = row.value
    session.close()
    return settings_dict

def set_settings(settings_dict):
    status = ()
    for key in settings_dict:
        if settings_dict[key] != "":
            if key == "c_n_boundary" or key == "eb_no_boundary":
                try:
                    float(settings_dict[key])
                except:
                    status = ("An error occurred while updating the " + key + ". Please check input value. ", False)
                    continue
            try:
                setting = session.query(Setting).filter_by(name = key).first()
                setting.value = settings_dict[key]
                session.commit()
                session.close()
                status = ("Data has been updated. " , True)
            except:
                status = ("An error occurred while updating the settings:" + key + ".", False)
    return status

def get_receivers(satellite = None, state = None):
    
    dict_settings = get_settings()
    c_n_boundary, eb_no_boundary = dict_settings["c_n_boundary"], dict_settings["eb_no_boundary"]

    list_of_data = []

    # Get all receivers
    if satellite is None and state is None:
        result = session.query(Receiver, Satellite, ReceiverType).filter(Receiver.satellite==Satellite.guid).filter(Receiver.model==ReceiverType.guid).all()
    # Get all active receivers
    if satellite is None and state is not None:
        result = session.query(Receiver, Satellite, ReceiverType).filter(Receiver.satellite==Satellite.guid).filter(Receiver.model==ReceiverType.guid).filter(Receiver.state==state).all()
    # Get specific receivers with satellites
    if satellite is not None and state is not None:
        result = session.query(Receiver, Satellite, ReceiverType).filter(Receiver.satellite==Satellite.guid).filter(Receiver.model==ReceiverType.guid).filter(Satellite.name==satellite).filter(Receiver.state==state).all()

    for r, s, r_t in result:
        d = dict(zip(keys, [r.guid, r.ip, r.port, r_t.model, s.name, r.login, r.password, r.state, r.time, r.c_n, r.eb_no, r.l_m, r.service]))
        d = check_value(d, c_n_boundary, eb_no_boundary)
        list_of_data.append(d)
    sortBySat = lambda list_of_data: list_of_data["satellite"]
    list_of_data.sort(key = sortBySat)
    session.close()
    return list_of_data

def get_satellites(name = None, guid = None):
    if name != None:
        sat = session.query(Satellite).filter(Satellite.name==name).all()
    if name == None:
        sat = session.query(Satellite).all()
    dict_satellites = dict()
    for row in sat:
        dict_satellites[row.guid] = row.name
    session.close()
    return dict_satellites

def get_receiver_authentication(model = None):
    if model != None:
        res = session.query(ReceiverType).filter(ReceiverType.model==model).all()
    if model == None:
        res = session.query(ReceiverType).all()
    dict_receiver_models = dict()
    for row in res:
        dict_receiver_models[row.model] = [row.login, row.password, row.guid]
    session.close()
    return dict_receiver_models

def add_receiver(ip, model, satellite, login, password, port, state):
    status = ()
    if state == "used":
        state = True
    if state == "don't used":
        state = False
    try:
        ipaddress.ip_address(ip)
    except:
        return "Invalid IP address."
    try:
        count = session.query(Receiver).filter(Receiver.ip==ip).filter(Receiver.port==str(port)).count()
        if count == 0:
            guid = str(uuid.uuid4())
            not_init = "new"
            # guid | ip | port | model | satellite | login | password | state |  c_n | eb_no | l_m | time
            # Get guides from satellite and models
            guid_sat = list(get_satellites(name = satellite).items())[0][0]
            guid_mod = get_receiver_authentication(model = model)[model][2]
            receiver = Receiver(guid = guid,ip = ip,port = port,model = guid_mod,satellite = guid_sat,login = login,password = password,state = state,c_n = not_init,eb_no = not_init,l_m = not_init,time = not_init)
            session.add(receiver)
            session.commit()
            status = ("Receiver has been added.", True)
        else:
            status =  ("IP and port exists.", False)
    except BaseException as err:
        print("here", err)
        status = ("An error occurred while adding the receiver.", False)
    session.close()
    return status

def delete_receiver(ip, port):
    status =()
    try:
        receiver = session.query(Receiver).filter(Receiver.ip==ip).filter(Receiver.port==port).one()
        session.delete(receiver)
        session.commit()
        status = ("Receiver has been deleted", True)
    except BaseException as err:
        print(err)
        status = ("An error occurred while deleting the receiver.",False)
    session.close()
    return status

def load_db_settings():
    try:
        with open("web/settings.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Failed to load settings. Check the correctness of the settings file 'web/settings.json'.")
    path = data["dialect"] + "+" + data["driver"] + "://" + data["user"] + ":" + data["password"] + "@" + data["host"] + ":" + data["port"] + "/" + data["dbname"]
    return path

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
        return status

    # HERE
    def set_receiver_authentication(self, receiver, login, password):
        s1, s2 = (), ()
        # Get old data
        old_data = get_receiver_authentication(model = receiver)
        #print(old_data)
        with self.engine.connect() as conn:
            try:
                metadata = sa.MetaData()
                receiver_models = sa.Table('receiver_models', metadata, autoload = True, autoload_with = conn)
                if login != old_data[receiver][0]:
                    query = sa.update(receiver_models).values(login = login)
                    query = query.where(receiver_models.columns.model == receiver)
                    ResultProxy = conn.execute(query)
                if password != old_data[receiver][1]:
                    query = sa.update(receiver_models).values(password = password)
                    query = query.where(receiver_models.columns.model == receiver)
                    ResultProxy = conn.execute(query)
                s1 = ("The data has been updated.", True)
            except:
                s2 = ("An error occurred while updating the data.", False)
        self.engine.dispose()
        return (s1, s2)
        
    def get_receiver(self, ip, port):
        status = ""
        d = dict()
        dict_settings = get_settings()
        c_n_boundary, eb_no_boundary = dict_settings["c_n_boundary"], dict_settings["eb_no_boundary"]
        with self.engine.connect() as conn:
            try:
                metadata = sa.MetaData()
                receivers = sa.Table('receivers', metadata, autoload = True, autoload_with = conn)
                satellites = sa.Table('satellites', metadata, autoload = True, autoload_with = conn)
                models = sa.Table('receiver_models', metadata, autoload = True, autoload_with = conn)
                
                query = sa.select([receivers.columns.guid, receivers.columns.ip, receivers.columns.port, models.columns.model, satellites.columns.name, receivers.columns.login, receivers.columns.password, receivers.columns.state, receivers.columns.time, receivers.columns.c_n, receivers.columns.eb_no, receivers.columns.l_m, receivers.columns.service])
                #query = sa.select([receivers])
                query = query.select_from(receivers.join(satellites, receivers.columns.satellite == satellites.columns.guid).join(models, receivers.columns.model == models.columns.guid))
                query = query.where(receivers.columns.ip == ip)
                query = query.where(receivers.columns.port == port)
                #print(str(query))
                ResultProxy = conn.execute(query)
                ResultSet = ResultProxy.fetchall()
                for row in ResultSet:
                    d = dict(zip(keys, row))
                    d = check_value(d, c_n_boundary, eb_no_boundary)
                status = ("", True)
            except:
                status = ("An error occurred while getting the data from DB.", False)
            conn.close()
        self.engine.dispose()
        return (status, d)

    def update_receiver(self, ip, model, satellite, login, password, port, state):
        if state == "used":
            state = True
        if state == "don't used":
            state = False
        s1, s2, s3, s4 = (), (), (), ()
        with self.engine.connect() as conn:
            # Get guide from satellite
            guid_sat = list(get_satellites(name = satellite).items())[0][0]
            guid_mod = get_receiver_authentication(model = model)[model][2]
            #
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
                query = sa.update(receivers).values(model = guid_mod, satellite = guid_sat, state = state)
                query = query.where(receivers.columns.ip == ip)
                query = query.where(receivers.columns.port == port)
                ResultProxy = conn.execute(query)
                s4 = ("The model/satellite/state have been updated. ", True)
            except:
                s4 = ("An error occurred while updating the model/satellite/state. ", False)
        self.engine.dispose()
        return (s1, s2, s3, s4)

    def get_stats_for_api(self, ip, port, time):
        c_n = []
        eb_no = []
        date_time = []
        time = int(time)
        cur_t = datetime.now()

        with self.engine.connect() as conn:
            metadata = sa.MetaData()
            stats = sa.Table('statistics', metadata, autoload=True, autoload_with=conn)
            query = sa.select([stats])
            query = query.where(stats.columns.ip == ip)
            query = query.where(stats.columns.port == port)
            if time != 0:
                hours = timedelta(hours = time)
                limit_time = (cur_t - hours).isoformat()
                query = query.where(stats.columns.date_time >= limit_time)
            query = query.order_by(sa.asc(stats.columns.date_time))

            ResultProxy = conn.execute(query)
            ResultSet = ResultProxy.fetchall()
            for row in ResultSet:
                try:
                    c_n.append(float(row[2]))
                    eb_no.append(float(row[3]))
                    date_time.append(row[5])
                except BaseException as err:
                    # ??? 
                    if row[2] == "parsing error" or row[3] == "parsing error":
                        c_n.append(0)
                        eb_no.append(0)
                        date_time.append(row[5])
                        #print(err)
                        continue
                    elif row[2] == "connection error" or row[3] == "connection error":
                        c_n.append(-1)
                        eb_no.append(-1)
                        date_time.append(row[5])
                        #print(err)
                        continue
            conn.close()
        self.engine.dispose()

        # Make the plot
        fig, ax = plt.subplots(figsize=(4.3, 1.2), layout='constrained')  # Create a figure containing a single axes.

        max_value_y = max(max(c_n), max(eb_no))
        min_value_y = min(min(c_n), min(eb_no))
        
        t = [min(date_time), max(date_time)]
        plt.xticks(t,t)

        #plt.xticks(np.arange(min(date_time), max(date_time), 1.0))
        #plt.yticks(np.arange(0, round(max_value_y), 2))
        plt.ylim([min_value_y - 1, max_value_y + 1])
        plt.xticks(fontsize=9)
        plt.yticks(fontsize=9)

        ax.plot(date_time, c_n, 'b', label = "C/N")  # Plot some data on the axes
        ax.plot(date_time, eb_no, 'r', label = "Eb/NO")  # Plot more data on the axes
        if time == 1 or time == 6 or time == 12 or time == 24:
            myFmt = mdates.DateFormatter('%H:%M')
        elif time == 0:
            myFmt = mdates.DateFormatter('%d/%m %H:%M')
        ax.xaxis.set_major_formatter(myFmt)

        if time == 0:
            time_desc = "Time (all saved data)"
        else:
            time_desc = "Time, last " + str(time) + " hour(s)"
        #ax.set_xlabel(time_desc)  # Add an x-label to the axes
        ax.set_ylabel('Values (dB)', fontdict = {'fontsize': 9, 'fontweight': 'normal'})  # Add a y-label to the axes
        ax.set_title("ip:" + ip + " port:" + port, fontdict = {'fontsize': 9, 'fontweight': 'normal'})  # Add a title to the axes
        
        # Show the service
        '''
        status, receiver = self.get_receiver(ip, port)
        list_for_services = ['proview2962', 'proview7100mnew', 'proview8130']
        if receiver["model"] in list_for_services:
            ax.text(date_time[0], (min_value_y + max_value_y)/2, receiver["service"] + '"', style='italic', fontsize=7, bbox={'facecolor': 'green', 'alpha': 0.2, 'pad': 3})
        '''

        ax.legend(fontsize = 8);  # Add a legend
        
        output = io.BytesIO()
        FigureCanvasAgg(fig).print_png(output)
        return output.getvalue()


    def get_stats(self, ip, port, time):
        c_n = []
        eb_no = []
        l_m = []
        date_time = []
        time = int(time)
        cur_t = datetime.now()
        
        with self.engine.connect() as conn:
            metadata = sa.MetaData()
            stats = sa.Table('statistics', metadata, autoload=True, autoload_with=conn)
            query = sa.select([stats])
            query = query.where(stats.columns.ip == ip)
            query = query.where(stats.columns.port == port)
            if time != 0:
                hours = timedelta(hours = time)
                limit_time = (cur_t - hours).isoformat()
                query = query.where(stats.columns.date_time >= limit_time)
            query = query.order_by(sa.asc(stats.columns.date_time))
            
            # Get current time
            #dt = datetime.datetime.now().strftime("%G %b %d %H:%M")
            
            ResultProxy = conn.execute(query)
            ResultSet = ResultProxy.fetchall()
            for row in ResultSet:
                try:
                    c_n.append(float(row[2]))
                    eb_no.append(float(row[3]))
                    date_time.append(row[5])
                except BaseException as err:
                    # ???
                    if row[2] == "parsing error" or row[3] == "parsing error":
                        c_n.append(0)
                        eb_no.append(0)
                        date_time.append(row[5])
                        #print(err)
                        continue
                    elif row[2] == "connection error" or row[3] == "connection error":
                        c_n.append(-1)
                        eb_no.append(-1)
                        date_time.append(row[5])
                        #print(err)
                        continue

            conn.close()
        self.engine.dispose()

        # Make the plot
        fig, ax = plt.subplots(figsize=(10, 2.7), layout='constrained')  # Create a figure containing a single axes.
        #plt.xticks(rotation=90)

        max_value_y = max(max(c_n), max(eb_no))
        min_value_y = min(min(c_n), min(eb_no))
        
        #plt.xticks(np.arange(0, len(date_time), 5))
        plt.yticks(np.arange(round(min_value_y), round(max_value_y), 1))

        ax.plot(date_time, c_n, label='C/N')  # Plot some data on the axes.
        ax.plot(date_time, eb_no, label='Eb/NO')  # Plot more data on the axes...
        #ax.plot(date_time, l_m, label='Link Margin')  # ... and some more.
        if time == 0:
            time_desc = "Time (all saved data)"
        else:
            time_desc = "Time, last " + str(time) + " hour(s)"
        ax.set_xlabel(time_desc)  # Add an x-label to the axes.
        ax.set_ylabel('Values (dB)')  # Add a y-label to the axes.
        ax.set_title("ip:" + ip + " port:" + port)  # Add a title to the axes.
        
        # Show the service
        status, receiver = self.get_receiver(ip, port)
        list_for_services = ['proview2962', 'proview7100mnew', 'proview8130']
        if receiver["model"] in list_for_services:
            ax.text(date_time[0], (min_value_y + max_value_y)/2, receiver["service"] + '"', style='italic', fontsize=9, bbox={'facecolor': 'green', 'alpha': 0.2, 'pad': 3})

        ax.legend();  # Add a legend.
        output = io.BytesIO()
        FigureCanvasAgg(fig).print_png(output)
        return output.getvalue()
