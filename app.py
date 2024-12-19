import flask
from flask import Flask, redirect, url_for
import os
import calendar


import database.database as database

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = (f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

database.db.init_app(app) # (1) flask prend en compte la base de donnee


with app.test_request_context(): # (2) bloc exécuté à l'initialisation de Flaskx
 database.init_database()


@app.route('/')
def hello_world():  # put application's code here
    return flask.render_template('home.html.jinja2')

@app.route('/connexion')
def connexion():
    return flask.render_template('connexion.html.jinja2')

@app.route('/inscription')
def inscription():
    return flask.render_template('inscription.html.jinja2')

if __name__ == '__main__':
    app.run()