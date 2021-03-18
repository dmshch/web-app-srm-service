# Copyright © 2020 Dmitrii Shcherbakov. All rights reserved.

from flask import Flask
from flask import request
from flask import redirect, url_for
from flask import render_template
from flask import flash
from web import dbsqlalch
import datetime

app = Flask(__name__)

# ------------------------------------------
# Here only for testing 
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
# ------------------------------------------

@app.route('/')
def index():
    return render_template('index.html', name='Main', time=get_time())

@app.route('/satellite/<satellite>')
def monitoring(satellite):
    name = satellite
    if name == "monitoring":
        final_list = dbsqlalch.get_data_receivers(state = True)
        name = "Monitoring"
    else:
        final_list = dbsqlalch.get_data_receivers(satellite = name, state = True)
    return render_template('index.html', name= name, time= get_time(), final_list= final_list)
    
@app.route('/receivers', methods=['POST', 'GET'])
def receivers():
    final_list = dbsqlalch.get_data_receivers()
    return render_template('index.html', name='Receivers', time=get_time(), list_of_receivers=final_list)

@app.route('/add', methods=['POST'])
def add():
    status = dbsqlalch.add(request.form['ip'], request.form['model'], request.form['satellite'], request.form['login'], request.form['password'], request.form['port'], request.form['state'])
    flash(status)
    return redirect(url_for('receivers'))

@app.route('/edit/<ip>/<port>/<action>',  methods=['POST', 'GET'])
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
def settings(path):
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
