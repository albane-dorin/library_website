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
def home():  # put application's code here
    recents = database.db.session.query(database.Book).order_by(database.Book.date.desc())[:50]
    best = database.db.session.query(database.Book).order_by(database.Book.grade.desc())[:50]
    r_author = {}
    b_author = {}
    for b in recents:
        r_author[b.author_id] = database.db.session.query(database.Author.complete_name).filter(database.Author.id == b.author_id).first()
    for b in best:
        b_author[b.author_id] = database.db.session.query(database.Author.complete_name).filter(database.Author.id == b.author_id).first()
    return flask.render_template('home.html.jinja2', recents=recents, r_author =r_author , best=best, b_author=b_author)

@app.route('/connexion')
def connexion():
    return flask.render_template('connexion.html.jinja2')

@app.route('/inscription')
def inscription():
    return flask.render_template('inscription.html.jinja2')

if __name__ == '__main__':
    app.run()