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

keys = ('guid', 'ip', 'port', 'model', 'satellite', 'login', 'password', 'state', 'time', 'c_n', 'eb_no', 'l_m', 'service')

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

    def get_receivers(self, satellite = None, state = None):

        with self.engine.connect() as conn:

            metadata = sa.MetaData()
            receivers = sa.Table('receivers', metadata, autoload = True, autoload_with = conn)
            satellites = sa.Table('satellites', metadata, autoload = True, autoload_with = conn)
            models = sa.Table('receiver_models', metadata, autoload = True, autoload_with = conn)

            dict_settings = self.get_settings()
            c_n_boundary, eb_no_boundary = dict_settings["c_n_boundary"], dict_settings["eb_no_boundary"]

            list_of_data = []

            query = sa.select([receivers.columns.guid, receivers.columns.ip, receivers.columns.port, models.columns.model, satellites.columns.name, receivers.columns.login, receivers.columns.password, receivers.columns.state, receivers.columns.time, receivers.columns.c_n, receivers.columns.eb_no, receivers.columns.l_m])
            query = query.select_from(receivers.join(satellites, receivers.columns.satellite == satellites.columns.guid).join(models, receivers.columns.model == models.columns.guid))

            if satellite is None and state is not None:
                query = query.where(receivers.columns.state == state)
            if satellite is not None and state is not None:
                 query = query.where(receivers.columns.state == state)
                 query = query.where(satellites.columns.name == satellite)
            ResultProxy = conn.execute(query)
            ResultSet = ResultProxy.fetchall()

            for row in ResultSet:
                #print(row)
                d = dict(zip(keys, row))
                d = self.check_value(d, c_n_boundary, eb_no_boundary)
                list_of_data.append(d)
            sortBySat = lambda list_of_data: list_of_data["satellite"]
            list_of_data.sort(key = sortBySat)
            conn.close()
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
                        status = ("Data has been updated. " , True)
                    except:
                        status = ("An error occurred while updating the settings:" + key + ".", False)
        self.engine.dispose()
        return status

    def get_satellites(self, name = None, guid = None):
        with self.engine.connect() as conn:
            metadata = sa.MetaData()
            satellites = sa.Table('satellites', metadata, autoload=True, autoload_with=conn)
            if name != None:
                query = sa.select([satellites]).where(satellites.columns.name == name)
            if name == None:
                query = sa.select([satellites])
            ResultProxy = conn.execute(query)
            ResultSet = ResultProxy.fetchall()
            dict_satellites = dict()
            for row in ResultSet:
                dict_satellites[row[0]] = row[1]
            self.engine.dispose()
            return dict_satellites

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
    
    def get_receiver_authentication(self, model = None):
        with self.engine.connect() as conn:
            metadata = sa.MetaData()
            receiver_models = sa.Table('receiver_models', metadata, autoload = True, autoload_with = conn)
            query = sa.select([receiver_models])
            if model != None:
                query = query.where(receiver_models.columns.model == model)
            ResultProxy = conn.execute(query)
            ResultSet = ResultProxy.fetchall()
            dict_receiver_models = dict()
            for row in ResultSet:
                dict_receiver_models[row[1]] = [row[2],row[3],row[0]]
            self.engine.dispose()
            return dict_receiver_models

    # HERE
    def set_receiver_authentication(self, receiver, login, password):
        s1, s2 = (), ()
        # Get old data
        old_data = self.get_receiver_authentication(model = receiver)
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
        status = ()
        if user != None and password != "":
            with self.engine.connect() as conn:
                try:
                    metadata = sa.MetaData()
                    users = sa.Table('users', metadata, autoload = True, autoload_with = conn)
                    query = sa.update(users).values(password = password)
                    query = query.where(users.columns.login == user)
                    ResultProxy = conn.execute(query)
                except:
                    status = ("An error occurred while updating the password.", False)
        if user == None:
            status = ("An error occurred while updating the password: you must choose the username. ", False)
        if passwd == "":
            status = ("An error occurred while updating the password: you must enter the password. ", False)
        self.engine.dispose()
        return status

    def add_receiver(self, ip, model, satellite, login, password, port, state):
        status = ()
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
                    # Get guide from satellite
                    guid_sat = list(self.get_satellites(name = satellite).items())[0][0]
                    guid_mod = self.get_receiver_authentication(model = model)[model][2]
                    query = sa.insert(receivers).values(guid = guid, ip = ip, port = port, model = guid_mod, satellite = guid_sat, login = login, password = password, state = state, c_n = not_init, eb_no = not_init, l_m = not_init, time = not_init)
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
                    d = self.check_value(d, c_n_boundary, eb_no_boundary)
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
            guid_sat = list(self.get_satellites(name = satellite).items())[0][0]
            guid_mod = self.get_receiver_authentication(model = model)[model][2]
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
                    print(err)
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
        status, receiver = self.get_receiver(ip, port)
        print(receiver)
        if receiver["model"] == "proview2962":
            ax.text(date_time[0], (min_value_y + max_value_y)/2, 'Service: "' + receiver["service"] + '"', style='italic', fontsize=7, bbox={'facecolor': 'green', 'alpha': 0.2, 'pad': 3})
        
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
                    l_m.append(float(row[4]))
                    #d_t = datetime.strptime(row[5], '%Y %b %d %H:%M')
                    #date_time.append(str(d_t.hour) + ":" + str(d_t.minute))
                    date_time.append(row[5])
                except BaseException as err:
                    print(err)
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
        if receiver["model"] == "proview2962":
            ax.text(date_time[0], (min_value_y + max_value_y)/2, 'Service: "' + receiver["service"] + '"', style='italic', fontsize=9, bbox={'facecolor': 'green', 'alpha': 0.2, 'pad': 3})

        ax.legend();  # Add a legend.
        output = io.BytesIO()
        FigureCanvasAgg(fig).print_png(output)
        return output.getvalue()
