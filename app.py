import flask
from flask import Flask, redirect, url_for
import os
from datetime import datetime
import calendar
from sqlalchemy import or_, and_


import database.database as database

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = (f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

database.db.init_app(app) # (1) flask prend en compte la base de donnee


with app.test_request_context(): # (2) bloc exécuté à l'initialisation de Flaskx
 database.init_database()
 genres = database.list_genres()


cached_research = {
    'query': None,
    'filters': {},
    'results': [],
    'total': 0
}

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

def research_book(query, genre, grade, date):
    grade= grade.split('/')
    if grade[1] == "above":
        result = database.db.session.query(database.Book).filter(
            and_(
                database.Book.title.like("%{}%".format(query)),
                database.Book.grade > grade[0],
            )).all()
    else:
        result = database.db.session.query(database.Book).filter(
            and_(
                database.Book.title.like("%{}%".format(query)),
                database.Book.grade < grade[0],
            )).all()
    if genre:
        genre = genre.split('/')[:-1]
        for b in result[:]:
            bgenres = [(g.split(',')[0]).split('-')[0] for g in b.genres.split(';')[:-1]]
            isin = False
            for g in genre:
                if g in bgenres:
                    isin = True
                    break
            if not isin:
                result.remove(b)
    if date:
        date = date.split('/')
        if date[1] == 'after':
            filter_result = [b for b in result if b.date and b.date.year>int(date[0])]
        else:
            filter_result = [b for b in result if b.date and b.date.year<int(date[0])]
        return filter_result, len(filter_result)
    return result, len(result)


@app.route('/')
def home():
    user = flask.request.args.get('user_id')
    if user:
        user = database.db.session.query(database.User).filter(database.User.id == user).first()

    recents = database.db.session.query(database.Book).order_by(database.Book.date.desc())[:50]
    best = database.db.session.query(database.Book).order_by(database.Book.grade.desc())[:50]
    r_author = {}
    b_author = {}
    for b in recents:
        r_author[b.author_id] = database.db.session.query(database.Author.complete_name).filter(database.Author.id == b.author_id).first()
    for b in best:
        b_author[b.author_id] = database.db.session.query(database.Author.complete_name).filter(database.Author.id == b.author_id).first()
    return flask.render_template('home.html.jinja2', recents=recents, r_author =r_author , best=best, b_author=b_author, genres=genres, user=user)


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

@app.route('/close-up/<int:book_id>', methods=["GET", "POST"])
def close_up(book_id):
    user = flask.request.args.get('user_id')
    if user:
        user = database.db.session.query(database.User).filter(database.User.id == user).first()

    book = database.db.session.query(database.Book).filter(database.Book.id == book_id).first()
    author = database.db.session.query(database.Author).filter(database.Author.id ==book.author_id).first()
    return flask.render_template("book.html.jinja2", book=book, author=author, genres=genres, user=user)

@app.route('/search/<int:nr>/<string:query>', methods=["GET", "POST"])
def search(nr, query):
    user = flask.request.args.get('user_id')
    if user:
        user = database.db.session.query(database.User).filter(database.User.id == user).first()

    global cached_research
    if query== 'noQueryEntered-ReturnAllMatchingFilter':
        query=''
    genre = flask.request.args.get('genre')
    grade = flask.request.args.get('grade')
    date = flask.request.args.get('date')
    if cached_research['query']!=query or cached_research['filters']!= {'genre': genre, 'date': date, 'grade': grade}:
        results, total = research_book(query, genre, grade, date)
        cached_research={
            'query': query,
            'filters': {'genre': genre, 'date': date, 'grade': grade},
            'results': results,
            'total': total
        }
    pages = cached_research['total']//60 + 1
    author={}
    for b in cached_research['results'][60*(nr-1):60*nr]:
        author[b.author_id] = database.db.session.query(database.Author.complete_name).filter(
            database.Author.id == b.author_id).first()

    return flask.render_template("search.html.jinja2", query=query, nr=nr, results=cached_research['results'][60*(nr-1):60*nr], total=cached_research['total'], pages=pages, author=author,
                                 genres=genres, genre=genre, date=date, grade=grade, user=user)

if __name__ == '__main__':
    app.run()

