# Copyright © 2020 Dmitrii Shcherbakov. All rights reserved.

import sqlalchemy as sa
import ipaddress
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
from .stat_model import Stat
from . import database

session = database.SessionLocal()

keys = ('guid', 'ip', 'port', 'model', 'satellite', 'login', 'password', 'state', 'time', 'c_n', 'eb_no', 'l_m', 'service', 'cc_delta')

def check_value(d, c_n_boundary, eb_no_boundary):
    if d["c_n"]  == "connection error" or d['eb_no'] == "connection error":
        d["alarm"] = "alarm_medium"
    elif d["c_n"]  == "new" or d['eb_no'] == "new":
        d["alarm"] = "alarm_low"
    elif d["c_n"] == "0.0" or d["c_n"] == "0" or d['eb_no'] == "0.0" or d['eb_no'] == "0" or d["c_n"] == "parsing error" or d['eb_no'] == "parsing error":
        d["alarm"] = "alarm_critical"
        # need try
    elif float(d["c_n"]) <= float(c_n_boundary) or float(d["eb_no"]) <= float(eb_no_boundary) or float(d["cc_delta"]) >= 1000:
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
        d = dict(zip(keys, [r.guid, r.ip, r.port, r_t.model, s.name, r.login, r.password, r.state, r.time, r.c_n, r.eb_no, r.l_m, r.service, r.cc_delta]))
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

def add_satellite(satellite):
    satellite = satellite.strip()
    status = ()
    try:
        if satellite != "":
            count = session.query(Satellite).filter(Satellite.name==satellite).count()
            if count == 0:
                guid = str(uuid.uuid4())
                satellite = Satellite(guid=guid, name=satellite)
                session.add(satellite)
                status = ("Satellite has been added", True)
            else:
                status =  ("Satellite exists.", False)
    except:
        status = ("An error occurred while adding the receiver.", False)
    session.commit()
    session.close()
    return status

def delete_satellite(satellite):
	status =()
	try:
		count = session.query(Receiver, Satellite).filter(Receiver.satellite==Satellite.guid).filter(Satellite.name==satellite).count()
		if count == 0:
			satellite = session.query(Satellite).filter(Satellite.name==satellite).one()
			session.delete(satellite)
			session.commit()
			status = ("Satellite has been deleted", True)
		else:
			status = (f"{satellite} exists in the table receivers. You must delete this binding between all receivers and {satellite}.",False)
	except BaseException as err:
		status = ("An error occurred while deleting the satellite.",False)
	session.close()
	return status
						
def update_satellite(oldsatellite, newsatellite):
	status =()
	try:
		count = session.query(Satellite).filter(Satellite.name==newsatellite).count()
		if count == 0:
			satellite = session.query(Satellite).filter_by(name = oldsatellite).first()
			satellite.name = newsatellite
			session.commit()
			status = ("Satellite has updated.", True)
		else:
			status = ("The name {newsatellite} exists", False)
	except BaseException as err:
		status = ("An error occurred while updating the satellite.",False)
	session.close()
	return status

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

def set_receiver_authentication(model, login, password):
    """Setting new login and password that must be not empty."""
    status = ()
    # Get old data
    old_data = get_receiver_authentication(model = model)
    try:
        if login != "" and password != "":
            model_type = session.query(ReceiverType).filter_by(model = model).first()
            if login != old_data[model][0]:
                model_type.login = login
            if password != old_data[model][1]:
                model_type.password = password
            session.commit()
            status = ("The data has been updated.", True)
        else:
            status = ("New login and password must be not empty.", False)
    except:
        status = ("An error occurred while updating the data.", False)
    session.close()
    return status

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
        #print("here", err)
        status = ("An error occurred while adding the receiver.", False)
    session.close()
    return status

def get_receiver(ip, port):
    status = ""
    d = dict()
    dict_settings = get_settings()
    c_n_boundary, eb_no_boundary = dict_settings["c_n_boundary"], dict_settings["eb_no_boundary"]
    try:
        result = session.query(Receiver, Satellite, ReceiverType).filter(Receiver.satellite==Satellite.guid).filter(Receiver.model==ReceiverType.guid).filter(Receiver.ip==ip).filter(Receiver.port==port).all()
        for r, s, r_t in result:
            d = dict(zip(keys, [r.guid, r.ip, r.port, r_t.model, s.name, r.login, r.password, r.state, r.time, r.c_n, r.eb_no, r.l_m, r.service, r.cc_delta]))
            d = check_value(d, c_n_boundary, eb_no_boundary)
        status = ("", True)
    except BaseException as err:
        #print(err)
        status = ("An error occurred while getting the data from DB.", False)
    return (status, d)

def update_receiver(ip, model, satellite, login, password, port, state):
    if state == "used":
        state = True
    if state == "don't used":
        state = False
    s1, s2 = (), ()
    # Get guide from satellite
    guid_sat = list(get_satellites(name = satellite).items())[0][0]
    guid_mod = get_receiver_authentication(model = model)[model][2]
    print(guid_sat, guid_mod)
    receiver = session.query(Receiver).filter(Receiver.ip==ip).filter(Receiver.port==port).first()
    try:
        if login != "" and password != "":
            receiver.login = login
            receiver.password = password
            session.commit()
            s1 = ("The login/password have been updated. ", True)
    except:
        s1 = ("An error occurred while updating the receiver (login/password)", False)
    try:
        receiver.satellite = guid_sat
        receiver.model = guid_mod
        receiver.state = state
        session.commit()
        s2 = ("The model/satellite/state have been updated. ", True)
    except:
        s2 = ("An error occurred while updating the model/satellite/state. ", False)
    session.close()
    return (s1, s2)

def delete_receiver(ip, port):
    status =()
    try:
        receiver = session.query(Receiver).filter(Receiver.ip==ip).filter(Receiver.port==port).one()
        session.delete(receiver)
        session.commit()
        status = ("Receiver has been deleted", True)
    except BaseException as err:
        #print(err)
        status = ("An error occurred while deleting the receiver.",False)
    session.close()
    return status

def get_stats_for_api(ip, port, time):
    
    c_n, eb_no, date_time = prepare_data_for_plots(ip, port, time)
    
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
    time = int(time)
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

    ax.legend(fontsize = 8);  # Add a legend
        
    output = io.BytesIO()
    FigureCanvasAgg(fig).print_png(output)
    return output.getvalue()

def get_stats(ip, port, time):

    c_n, eb_no, date_time = prepare_data_for_plots(ip, port, time)

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
    
    ax.legend();  # Add a legend.
    output = io.BytesIO()
    FigureCanvasAgg(fig).print_png(output)
    return output.getvalue()

def prepare_data_for_plots(ip, port, time):
    time = int(time)
    # Lists for plot
    #Y scale
    c_n = []
    eb_no = []
    # X scale
    date_time = []

    time_interval = int(time)
    current_time = datetime.now()

    if time != 0:
        delta = timedelta(hours = time_interval)
        limit = (current_time - delta).isoformat()
        stats = session.query(Stat).filter(Stat.ip==ip).filter(Stat.port==port).filter(Stat.date_time>=limit).order_by(Stat.date_time).all()
    elif time == 0:
        stats = session.query(Stat).filter(Stat.ip==ip).filter(Stat.port==port).order_by(Stat.date_time).all()
    for row in stats:
        try:
            c_n.append(float(row.c_n))
            eb_no.append(float(row.eb_no))
            date_time.append(row.date_time)
        except BaseException as err:
            if row.c_n == "parsing error" or row.eb_no == "parsing error":
                c_n.append(0)
                eb_no.append(0)
                date_time.append(row.date_time)
                #print(err)
                continue
            elif row.c_n == "connection error" or row.eb_no == "connection error":
                c_n.append(-1)
                eb_no.append(-1)
                date_time.append(row.date_time)
                #print(err)
                continue
    return (c_n, eb_no, date_time)
