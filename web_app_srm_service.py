# Copyright © 2020 Dmitrii Shcherbakov. All rights reserved.

from flask import Flask
from flask import request
from flask import redirect, url_for
from flask import render_template
from flask import flash
from flask import send_file
from flask import Response
from web import dbsqlalch
from web import settings
from web import users
import flask_login
import datetime
import json
import bcrypt

application = Flask(__name__)

data = settings.load_settings()
application.secret_key = data["secret_key"]

login_manager = flask_login.LoginManager()
login_manager.init_app(application)

# load users from db
users_dict = dbsqlalch.get_user_authentication()

@login_manager.user_loader
def user_loader(login):
    if login not in users_dict:
        return

    user = users.User()
    user.id = login
    return user

def check_access():
     if flask_login.current_user.get_id() == "monitor":
          flash("You do not have permission to view this page.")
          values = dbsqlalch.get_settings()
          return False

# HERE FOR CHECK LOGIN
@application.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'GET':
		return render_template('login.html')
	if request.method == 'POST' and request.form['login'] != "" and request.form['password'] != "":
		login  = request.form['login']
		password = request.form['password']
		if bcrypt.checkpw(password.encode("utf-8"), bytes(users_dict[login].encode("utf-8"))):
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
    values = dbsqlalch.get_settings()
    return render_template('index.html', name = 'Main', values = values, user = flask_login.current_user.get_id())
 
@application.route('/monitoring/<satellite>')
@flask_login.login_required
def monitoring(satellite):
     satellites = dbsqlalch.get_satellites()
     name = satellite
     if name == "all":
          final_list = dbsqlalch.get_receivers(state = True)
          name = "All"
     else:
          final_list = dbsqlalch.get_receivers(satellite = satellite, state = True)
     name = "Monitoring"
     final_list.sort(key = lambda final_list: final_list["ip"])
     final_list.sort(key = lambda final_list: final_list["satellite"])
     settings = dbsqlalch.get_settings()
     return render_template('index.html', name = name, final_list = final_list, settings = settings, satellites = satellites, satellite = satellite, user = flask_login.current_user.get_id())

# API v1.0 - GET ALL
@application.route('/api/v1.0/monitoring/')
def api_monitoring():
    in_list = dbsqlalch.get_receivers(state = True)
    settings_dict = dbsqlalch.get_settings()
    for item in in_list:
        [item.pop(key) for key in ['login', 'password', 'state', 'guid']]
        item['alarm_color'] = settings_dict[item['alarm']]
    out_json = json.dumps(in_list)
    return str(out_json)

# API v1.0 - GET ONE
@application.route('/api/v1.0/monitoring/<ip>/<port>')
def api_monitoring_ip_port(ip, port):
    status, receiver = dbsqlalch.get_receiver(ip, port)
    [receiver.pop(key) for key in ['login', 'password', 'state', 'guid']]
    out_json = json.dumps(receiver)
    return str(out_json)

# API v1.0 - GET STATISTICS FOR ONE RECEIVER
@application.route('/api/v1.0/monitoring/<ip>/<port>/<time>')
def api_monitoring_ip_port_stats(ip, port, time):
    data = dbsqlalch.get_stats_for_api(ip, port, time)
    return Response(data, mimetype='image/png')

# Get info about all receivers
@application.route('/receivers/', methods = ['GET'])
@flask_login.login_required
def get_receivers():
    types_of_receivers = dbsqlalch.get_receiver_authentication()
    satellites = dbsqlalch.get_satellites()
    final_list = dbsqlalch.get_receivers()
    final_list.sort(key = lambda final_list: final_list["ip"])
    final_list.sort(key = lambda final_list: final_list["satellite"])
    return render_template('index.html', name = 'Receivers', list_of_receivers = final_list, satellites = satellites, types_of_receivers = types_of_receivers, user = flask_login.current_user.get_id())

# Add new receiver
@application.route('/receivers/add', methods = ['POST'])
@flask_login.login_required
def create_receivers():
    message, status = dbsqlalch.add_receiver(request.form['ip'], request.form['model'], request.form['satellite'], request.form['login'], request.form['password'], request.form['port'], request.form['state'])
    flash(message, "normal" if status else "error")
    return redirect(url_for('get_receivers'))

# Get info about one receiver
@application.route('/receivers/<ip>/<port>', methods = ['GET'])
def get_receiver(ip, port):
    status = ""
    satellites = dbsqlalch.get_satellites()
    types_of_receivers = dbsqlalch.get_receiver_authentication()
    # receiver is dict -> keys: ip, model, satellite, login, password, port, state
    message_tuple, receiver = dbsqlalch.get_receiver(ip, port)
    message, status = message_tuple
    flash(message, "normal" if status else "error")
    return render_template('index.html', name='Edit', receiver=receiver, satellites= satellites, types_of_receivers = types_of_receivers, user = flask_login.current_user.get_id())

# Update or delete receiver
@application.route('/receivers/<ip>/<port>/<action>', methods = ['GET', 'POST'])
def modify_receiver(ip, port, action):
    if action == "update":
        message_tuple = dbsqlalch.update_receiver(ip, request.form['model'], request.form['satellite'], request.form['login'], request.form['password'], port, request.form['state'])
        for m in message_tuple:
            if len(m) != 0:
                message, status = m
                flash(message, "normal" if status else "error")
        return redirect(url_for('get_receivers'))
    if action == "delete":
        message, status = dbsqlalch.delete_receiver(ip, port)
        flash(message, "normal" if status else "error")
    return redirect(url_for('get_receivers'))

# Statistics fixed
@application.route('/statistics/<ip>/<port>/<start_time>/<end_time>', methods = ['GET', 'POST'])
def get_statistics(ip, port, start_time, end_time):
    current_time = datetime.datetime.now()
    delta = datetime.timedelta(days = 31)
    min_date = (current_time - delta).strftime("%Y-%m-%d")
    max_date = current_time.strftime("%Y-%m-%d")
    if request.method == 'GET':
        return render_template('plot.html', min_date = min_date, max_date = max_date, ip = ip, port = port, start_time = start_time, end_time = end_time, satellite = dbsqlalch.get_receiver(ip, port)[1]['satellite'])
    if request.method == 'POST':
        return render_template('plot.html', min_date = min_date, max_date = max_date, ip = ip, port = port, start_time = request.form['date_from'].replace("-", "."), end_time = request.form['date_to'].replace("-", "."), satellite = dbsqlalch.get_receiver(ip, port)[1]['satellite'])

# PLOT, PNG
@application.route("/matplot-as-image-<ip>-<port>-<start_time>-<end_time>.png")
def plot_png(ip, port, start_time, end_time):
    data = dbsqlalch.get_stats(ip, port, start_time, end_time)
    return Response(data, mimetype='image/png')

@application.route('/settings/receivers', methods=['GET'])
@flask_login.login_required
def settings_receivers_authentication():
	if check_access() is False:
		return render_template('index.html', name='Main', values= dbsqlalch.get_settings())
	path = "receivers"
	values = dbsqlalch.get_receiver_authentication()
	return render_template('index.html', name='Settings', path=path, subname=path.capitalize(), values=values, user = flask_login.current_user.get_id())	

@application.route('/settings/receivers/update', methods=['POST'])
@flask_login.login_required
def settings_update_receivers_authentication():
	if check_access() is False:
		return render_template('index.html', name='Main', values= dbsqlalch.get_settings())
	message_tuple = dbsqlalch.set_receiver_authentication(request.form.get('receiver_select'), request.form['login'] ,request.form['password'])
	if len(message_tuple) != 0:
		message, status = message_tuple
		flash(message, "normal" if status else "error")
	return redirect('/settings/receivers')

@application.route('/settings/users', methods=['GET'])
@flask_login.login_required
def settings_users():
	if check_access() is False:
		return render_template('index.html', name='Main', values= dbsqlalch.get_settings())
	path = "users"
	#values = dbsqlalch.get_user_authentication()
	return render_template('index.html', name='Settings', path=path, subname=path.capitalize(), user = flask_login.current_user.get_id())

@application.route('/settings/users/update', methods=['POST'])
@flask_login.login_required
def settings_update_users():
	if check_access() is False:
		return render_template('index.html', name='Main', values= dbsqlalch.get_settings())
	message_tuple = dbsqlalch.set_user_authentication(request.form.get('user_select'), request.form['password'])
	if len(message_tuple) != 0:
		message, status = message_tuple
		flash(message, "normal" if status else "error")
	return redirect('/settings/users')
	
@application.route('/settings/global', methods=['GET'])
@flask_login.login_required
def settings_global():
	path = "global"
	if check_access() is False:
		return render_template('index.html', name='Main', values= dbsqlalch.get_settings())
	values = dbsqlalch.get_settings()
	return render_template('index.html', name='Settings', path=path, subname=path.capitalize(), values=values, user = flask_login.current_user.get_id())

@application.route('/settings/global/update', methods=['POST'])
@flask_login.login_required
def settings_update_global():
	if check_access() is False:
		return render_template('index.html', name='Main', values= dbsqlalch.get_settings())
	message_tuple = dbsqlalch.set_settings(request.form)
	if len(message_tuple) != 0:
		message, status = message_tuple
		flash(message, "normal" if status else "error")
	return redirect('/settings/global')

@application.route('/settings/satellites/', methods=['GET'])
@flask_login.login_required
def settings_get_satellites():
	path = "satellites"
	if check_access() is False:
		return render_template('index.html', name='Main', values= dbsqlalch.get_settings())
	values = dbsqlalch.get_satellites()
	return render_template('index.html', name= 'Settings', path= path, subname= path.capitalize(), values= values, user = flask_login.current_user.get_id())

@application.route('/settings/satellites/add', methods=['POST'])
@flask_login.login_required
def settings_add_satellites():
	if check_access() is False:
		return render_template('index.html', name='Main', values= dbsqlalch.get_settings())
	message_tuple = dbsqlalch.add_satellite(request.form['satellite'])
	if len(message_tuple) != 0:
		message, status = message_tuple
		flash(message, "normal" if status else "error")
	return redirect('/settings/satellites/')

@application.route('/settings/satellites/update', methods=['POST'])
@flask_login.login_required
def settings_update_satellites():
	if check_access() is False:
		return render_template('index.html', name='Main', values= dbsqlalch.get_settings())
	message_tuple = dbsqlalch.update_satellite(request.form['oldsatellite'], request.form['newsatellite'])
	if len(message_tuple) != 0:
		message, status = message_tuple
		flash(message, "normal" if status else "error")
	return redirect('/settings/satellites/')

@application.route('/settings/satellites/delete', methods=['POST'])
@flask_login.login_required
def settings_delete_satellites():
	if check_access() is False:
		return render_template('index.html', name='Main', values= dbsqlalch.get_settings())
	message_tuple = dbsqlalch.delete_satellite(request.form['satellite'])
	if len(message_tuple) != 0:
		message, status = message_tuple
		flash(message, "normal" if status else "error")
	return redirect('/settings/satellites/')

@application.route('/time', methods=['GET'])
@flask_login.login_required
def time():
	return ("Local time: " + datetime.datetime.now().strftime("%H:%M"))

def get_time():
    return ("Local time: " + datetime.datetime.now().strftime("%H:%M"))
