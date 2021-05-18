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

app = Flask(__name__)

data = settings.load_settings()
app.secret_key = data["secret_key"]

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

# load users from db
users_dict = dbsqlalch.get_user_authentication()

@login_manager.user_loader
def user_loader(login):
    if login not in users_dict:
        return

    user = users.User()
    user.id = login
    return user

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    login  = request.form['login']
    if request.form['password'] == users_dict[login]:
        user = users.User()
        user.id = login
        flask_login.login_user(user)
        return render_template('index.html', name='Main', time=get_time())
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect(url_for('login'))

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('login.html')

@app.route('/')
@flask_login.login_required
def index():
    return render_template('index.html', name='Main', time=get_time())

@app.route('/satellite/<satellite>')
@flask_login.login_required
def monitoring(satellite):
    name = satellite
    if name == "monitoring":
        final_list = dbsqlalch.get_data_receivers(state = True)
        name = "Monitoring"
    else:
        final_list = dbsqlalch.get_data_receivers(satellite = name, state = True)
    return render_template('index.html', name= name, time= get_time(), final_list= final_list)
    
@app.route('/receivers', methods=['POST', 'GET'])
@flask_login.login_required
def receivers():
    final_list = dbsqlalch.get_data_receivers()
    sortBySat = lambda final_list: final_list["satellite"]
    final_list.sort(key = sortBySat)
    return render_template('index.html', name='Receivers', time=get_time(), list_of_receivers=final_list)

@app.route('/add', methods=['POST'])
@flask_login.login_required
def add():
    status = dbsqlalch.add(request.form['ip'], request.form['model'], request.form['satellite'], request.form['login'], request.form['password'], request.form['port'], request.form['state'])
    flash(status)
    return redirect(url_for('receivers'))

@app.route('/edit/<ip>/<port>/<action>',  methods=['POST', 'GET'])
@flask_login.login_required
def edit(ip, port, action):
    status = ""

    if action == "get":
        # receiver is dict -> keys: ip, model, satellite, login, password, port, state
        status, receiver = dbsqlalch.get(ip, port)
        return render_template('index.html', name='Edit', time=get_time(), receiver=receiver)

    if action == "update":
        if 'model' not in request.form or 'satellite' not in request.form or 'state' not in request.form:
            flash("Missing required value.")
            status, receiver = dbsqlalch.get(ip, port)
            return render_template('index.html', name='Edit', time=get_time(), receiver=receiver)
        status = dbsqlalch.update(ip, request.form['model'], request.form['satellite'], request.form['login'], request.form['password'], port, request.form['state'])
        flash(status)
        return redirect(url_for('receivers'))

    if action == "delete":
        status = dbsqlalch.delete(ip, port)
        flash(status)
        return redirect(url_for('receivers'))

@app.route('/settings/<path>', methods=['POST', 'GET'])
@flask_login.login_required
def settings(path):
    if flask_login.current_user.get_id() == "monitor":
        flash("You do not have permission to view this page.")
        return render_template('index.html', name='Main', time=get_time())
    status = ""
    values = dict()
    if path == "global":
        if request.method == 'GET':
            values = dbsqlalch.get_settings()
        if request.method == 'POST':
            status = dbsqlalch.set_settings(c_n =  request.form['CN'], eb_no = request.form['ebno'])
    elif path == "users":
        if request.method == 'GET':
            values = dbsqlalch.get_user_authentication()
        if request.method == 'POST':
            status = dbsqlalch.set_user_authentication(request.form.get('user_select'), request.form['password'])
    elif path == "receivers":
        if request.method == 'GET':
            values = dbsqlalch.get_receiver_authentication()
        if request.method == 'POST':
            status = dbsqlalch.set_receiver_authentication(request.form.get('receiver_select'), request.form['login'] ,request.form['password'])
    flash(status)
    if request.method == 'POST':
        return redirect('/settings/' + path)
    return render_template('index.html', name='Settings', time=get_time(), path=path, subname=path.capitalize(), values=values)

def get_time():
    return datetime.datetime.now().strftime("%H:%M")
