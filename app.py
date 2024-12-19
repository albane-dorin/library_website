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



#Cette fonction permet de vérifier la validité des formulaires d'inscription et de connexion
def form_valide(form, i):  # 0 pour connexion, 1 pour inscription
    result = True
    errors = []

    username = flask.request.form.get("username", "")
    p1 = flask.request.form.get("password", "")

    if username == "":
        return False, []

    if i == 0:

        user = database.db.session.query(database.User).filter(database.User.username == username).first()

        if user is None:
            result = False

        else:
            mdp = user.password
            if mdp != p1:
                result = False

        if not result:
            errors.append("Username or password incorrect")

    if i == 1:
        email = flask.request.form.get("email", "")
        p2 = flask.request.form.get("p2", "")

        # Test de validité

        if p1 == "" or p2 == "":
            result = False

        for user in database.User.query.all():
            if user.username == username:
                result = False
                errors += ["This username already exists, please choose another one"]
            elif user.mail == email:
                result = False
                errors += ["This email cannot be used"]

        if p1 != p2:
            result = False
            errors += ["Please write the same passwords"]

    return result, errors


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


@app.route('/connexion', methods=["GET", "POST"])
def connexion():
    form = flask.request.form

    # Récupère les résultats du test du questionnaires
    valide, errors = form_valide(form, 0)

    #Formulaire incorecte : On affiche la page avec les erreurs indiquées
    if not valide:
        return flask.render_template("connexion.html.jinja2", form=form, error=errors)

    #Formulaire valide : on récupère l'utilisateur dans la base de donnée pour rediriger vers la bonne vue
    else:
        user = database.db.session.query(database.User).filter(database.User.username == form.get("username", "")).first()
        return redirect(url_for('home', user_id=user.id))


@app.route('/inscription', methods=["GET", "POST"])
def inscription():
    form = flask.request.form

    # Récupère les résultats du test du questionnaires
    valide, errors = form_valide(form, 1)

    # Formulaire incorecte : On affiche la page avec les
    # erreurs indiquées
    if not valide:
        return flask.render_template("inscription.html.jinja2", form=form, error=errors)

    # Formulaire valide : On crée l'utilisateur et on le redirige vers la vue correspondant à son profil
    else:
        database.new_user(form.get("username", ""), form.get("password", ""), form.get("email", ""))

        user = database.db.session.query(database.User).filter(database.User.username == form.get("username", "")).first()

        return redirect(url_for('home', user_id=user.id))



if __name__ == '__main__':
    app.run()

