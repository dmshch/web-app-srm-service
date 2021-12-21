# Copyright © 2020 Dmitrii Shcherbakov. All rights reserved.

from flask import Flask
from flask import request
from flask import redirect, url_for
from flask import render_template
from flask import flash
from web import dbsqlalch
from web import settings
from web import users
import flask_login
import datetime
import json

application = Flask(__name__)

data = settings.load_settings()
application.secret_key = data["secret_key"]

login_manager = flask_login.LoginManager()
login_manager.init_app(application)

# load users from db
users_dict = dbsqlalch.DB().get_user_authentication()

@login_manager.user_loader
def user_loader(login):
    if login not in users_dict:
        return

    user = users.User()
    user.id = login
    return user

@application.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':
        login  = request.form['login']
        if request.form['password'] == users_dict[login]:
            user = users.User()
            user.id = login
            flask_login.login_user(user)
            return redirect(url_for('main'))
    return redirect(url_for('login'))

@application.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect(url_for('login'))

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('login.html')

@application.route('/main')
@application.route('/')
@flask_login.login_required
def main():
    values = dbsqlalch.DB().get_settings()
    return render_template('index.html', name = 'Main', time = get_time(), values = values)

# 
@application.route('/monitoring/<satellite>')
@flask_login.login_required
def monitoring(satellite):
    satellites = dbsqlalch.DB().get_satellites()
    name = satellite
    if name == "all":
        final_list = dbsqlalch.DB().get_receivers(state = True)
        name = "All"
    else:
        final_list = dbsqlalch.DB().get_receivers(satellite = satellite, state = True)
    final_list.sort(key = lambda final_list: final_list["ip"])
    final_list.sort(key = lambda final_list: final_list["satellite"])
    settings = dbsqlalch.DB().get_settings()
    return render_template('index.html', name = name, time = get_time(), final_list = final_list, settings = settings, satellites = satellites)

# API v1.0 - GET ALL
@application.route('/api/v1.0/monitoring/')
def api_monitoring():
    in_list = dbsqlalch.DB().get_receivers(state = True)
    for item in in_list:
        [item.pop(key) for key in ['login', 'password', 'state']]
    out_json = json.dumps(in_list)
    #print(out_json)
    return str(out_json)

# API v1.0 - GET ONE
@application.route('/api/v1.0/monitoring/<ip>/<port>')
def api_monitoring_ip_port(ip, port):
    status, receiver = dbsqlalch.DB().get_receiver(ip, port)
    [receiver.pop(key) for key in ['login', 'password', 'state']]
    out_json = json.dumps(receiver)
    return str(out_json)

# Get info about all receivers
@application.route('/receivers/', methods = ['GET'])
@flask_login.login_required
def get_receivers():
    types_of_receivers = dbsqlalch.DB().get_receiver_authentication()
    satellites = dbsqlalch.DB().get_satellites()
    final_list = dbsqlalch.DB().get_receivers()
    final_list.sort(key = lambda final_list: final_list["ip"])
    final_list.sort(key = lambda final_list: final_list["satellite"])
    return render_template('index.html', name = 'Receivers', time=get_time(), list_of_receivers = final_list, satellites = satellites, types_of_receivers = types_of_receivers)

# Add new receiver
@application.route('/receivers/', methods = ['POST'])
@flask_login.login_required
def create_receivers():
    message, status = dbsqlalch.DB().add_receiver(request.form['ip'], request.form['model'], request.form['satellite'], request.form['login'], request.form['password'], request.form['port'], request.form['state'])
    flash(message, "normal" if status else "error")
    return redirect(url_for('get_receivers'))

# Get info about one receiver
@application.route('/receivers/<ip>/<port>', methods = ['GET'])
def get_receiver(ip, port):
    status = ""
    satellites = dbsqlalch.DB().get_satellites()
    types_of_receivers = dbsqlalch.DB().get_receiver_authentication()
    # receiver is dict -> keys: ip, model, satellite, login, password, port, state
    message_tuple, receiver = dbsqlalch.DB().get_receiver(ip, port)
    message, status = message_tuple
    flash(message, "normal" if status else "error")
    return render_template('index.html', name='Edit', time=get_time(), receiver=receiver, satellites= satellites, types_of_receivers = types_of_receivers)

# Update or delete receiver
@application.route('/receivers/<ip>/<port>/<action>', methods = ['POST'])
def modify_receiver(ip, port, action):
    if action == "update":
        message_tuple = dbsqlalch.DB().update_receiver(ip, request.form['model'], request.form['satellite'], request.form['login'], request.form['password'], port, request.form['state'])
        for m in message_tuple:
            if len(m) != 0:
                message, status = m
                flash(message, "normal" if status else "error")
        return redirect(url_for('get_receivers'))
    if action == "delete":
        message, status = dbsqlalch.DB().delete_receiver(ip, port)
        flash(message, "normal" if status else "error")
    return redirect(url_for('get_receivers'))

@application.route('/settings/<path>', methods=['POST', 'GET'])
@flask_login.login_required
def settings(path):
    message_tuple = ()
    if flask_login.current_user.get_id() == "monitor":
        flash("You do not have permission to view this page.")
        values = dbsqlalch.DB().get_settings()
        return render_template('index.html', name='Main', time=get_time(), values= values)
    status = ""
    values = dict()
    if path == "global":
        if request.method == 'GET':
            values = dbsqlalch.DB().get_settings()
        if request.method == 'POST':
            message_tuple = dbsqlalch.DB().set_settings(request.form)
    elif path == "users":
        if request.method == 'GET':
            values = dbsqlalch.DB().get_user_authentication()
        if request.method == 'POST':
            message_tuple = dbsqlalch.DB().set_user_authentication(request.form.get('user_select'), request.form['password'])
    elif path == "receivers":
        if request.method == 'GET':
            values = dbsqlalch.DB().get_receiver_authentication()
        if request.method == 'POST':
            message_tuple = dbsqlalch.DB().set_receiver_authentication(request.form.get('receiver_select'), request.form['login'] ,request.form['password'])
    elif path == "satellites":
        if request.method == 'GET':
            values = dbsqlalch.DB().get_satellites()
        if request.method == 'POST':
            message_tuple = dbsqlalch.DB().add_satellites(request.form['satellite'])

    for m in message_tuple:
        if len(m) != 0:
            message, status = m
            flash(message, "normal" if status else "error")

    if request.method == 'POST':
        return redirect('/settings/' + path)
    return render_template('index.html', name='Settings', time=get_time(), path=path, subname=path.capitalize(), values=values)

def get_time():
    return datetime.datetime.now().strftime("%H:%M")
