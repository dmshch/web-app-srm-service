# Copyright © 2020 Dmitrii Shcherbakov. All rights reserved.

from flask import Flask
from flask import request
from flask import redirect, url_for
from flask import render_template
from flask import flash
import datetime
import json

app = Flask(__name__)

# ------------------------------------------
# Here only for testing 
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
# ------------------------------------------

@app.route('/')
def index():
    time = datetime.datetime.now().strftime("%H:%M")
    return render_template('index.html', name='Main', time=time)

@app.route('/satellite/<satellite>')
def monitoring(satellite):
    name = satellite
    time = datetime.datetime.now().strftime("%H:%M")
    if name == "monitoring":
        final_list = list_of_objects
        name = "Monitoring"
    else:
        final_list = [i for i in list_of_objects if i.satellite == name]
    return render_template('index.html', name = name, time=time, final_list = final_list)
    
@app.route('/receivers', methods=['POST', 'GET'])
def receivers():
    time = datetime.datetime.now().strftime("%H:%M")
    list_of_receivers = get_objects.get_objects_receivers("all")
    return render_template('index.html', name='Receivers', time=time, list_of_receivers=list_of_receivers)

@app.route('/add', methods=['POST'])
def add():
    status = add_data_in_db.add_data(request.form['ip'], request.form['model'], request.form['satellite'], request.form['login'], request.form['password'], request.form['port'], request.form['state'])
    flash(status)
    # add to the active list of receivers
    if status == "IP address and port have been added" and request.form['state'] == "used":
        obj = get_objects.return_object(request.form['ip'], request.form['model'], request.form['satellite'], request.form['login'], request.form['password'], request.form['port'], 1)
        list_of_objects.append(obj)
    return redirect(url_for('receivers'))

@app.route('/edit/<ip>/<port>/<action>',  methods=['POST', 'GET'])
def edit(ip, port, action):
    status = ""
    time = datetime.datetime.now().strftime("%H:%M")

    if action == "get":
        # receiver is dict -> keys: ip, model, satellite, login, password, port, state
        receiver = edit_db.select_receiver_for_edit(ip, port)
        return render_template('index.html', name='Edit', time=time, receiver=receiver)

    if action == "update":
        # update db
        status = edit_db.update_receiver(ip, request.form['model'], request.form['satellite'], request.form['login'], request.form['password'], port, request.form['state'])
        # check used or not. if used -> check in list_of_objects -> if exist -> remove, make obj and add-> if not -> make obj and add
        if request.form['state'] == "used":
            for obj in list_of_objects:
                if obj.ip == ip and obj.port == port:
                    list_of_objects.remove(obj)
            obj = get_objects.return_object(ip, request.form['model'], request.form['satellite'], request.form['login'], request.form['password'], port, 1)
            list_of_objects.append(obj)
        # if don't used -> check in list_of_objects -> if exist -> remove obj from list_of_objects
        elif request.form['state'] == "don't used":
            for obj in list_of_objects:
                if obj.ip == ip and obj.port == port:
                    list_of_objects.remove(obj)
        flash(status)
        return redirect(url_for('receivers'))

    if action == "delete":
        status = delete_data_from_db.delete_data(ip, port)
        flash(status)
        if status == "IP address and port have been removed":
            for obj in list_of_objects:
                if obj.ip == ip and obj.port == port:
                    list_of_objects.remove(obj)
        return redirect(url_for('receivers'))

@app.route('/settings/<path>', methods=['POST', 'GET'])
def settings(path):
    time = datetime.datetime.now().strftime("%H:%M")
    status = ""
    values = dict()
    if path == "global":
        if request.method == 'GET':
            values = edit_settings.get_global_settings()
        if request.method == 'POST':
            status = edit_settings.set_global_settings(request.form['time'], request.form['CN'], request.form['ebno'])
    elif path == "users":
        if request.method == 'GET':
            values = edit_settings.get_users_settings()
        if request.method == 'POST':
            status = edit_settings.set_users_settings(request.form['adminPassword'], request.form['monitorPassword'])
    elif path == "receivers":
        if request.method == 'GET':
            values = edit_settings.get_receivers_settings()
        if request.method == 'POST':
            pass
    print(values)
    flash(status)
    return render_template('index.html', name='Settings', time=time, path=path, subname=path.capitalize(), values=values)

