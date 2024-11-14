import flask
from flask import Flask

app = Flask(__name__)


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
