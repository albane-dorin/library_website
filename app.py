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
    'total': 0,
}


testl = {"one":10,"two":6,"three":6,"four":2,"five":1,"six":1}
testl = dict(sorted(testl.items(), key=lambda item: item[1]))
print(testl)
i=0
nb=0
for el in testl.items():
    if el[1]>nb:
        nb = el[1]
        i+=1
    testl[el[0]] = i
print(testl)


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

def research_book(query, genre, grade, date, quick):
    if quick:
        if quick == 'Best':
            result = database.db.session.query(database.Book).order_by(database.Book.grade.desc()).all()
        elif quick == 'New':
            result = database.db.session.query(database.Book).order_by(database.Book.date.desc()).all()
        elif quick == 'Romance':
            genre = 'romance/'
            result = database.db.session.query(database.Book).all()
        elif quick == 'Fantasy':
            genre='fantasy/'
            result = database.db.session.query(database.Book).all()

    else:
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

def find_fav_books(el, list, nb):
    if not el[0].grade:
        return list
    if not list[0]:
        list[0] = el
    elif el[0].grade>list[0][0].grade:
        list.insert(0, el)
    elif el[0].grade==list[0][0].grade and el[0].date >= list[0][0].date:
            list.insert(0, el)

    elif not list[1]:
        list[1]=el
    elif el[0].grade>list[1][0].grade and el[0].grade<=list[0][0].grade:
        list.insert(1, el)
    elif el[0].grade == list[1][0].grade and el[0].date >= list[1][0].date:
            list.insert(1, el)


    elif not list[2]:
        list[2]=el
    elif el[0].grade > list[2][0].grade and el[0].grade <= list[1][0].grade:
        list.insert(2, el)
    elif el[0].grade == list[2][0].grade and el[0].date >= list[2][0].date:
            list.insert(2, el)

    elif not list[3]:
        list[3]=el
    elif el[0].grade>list[3][0].grade and el[0].grade<=list[2][0].grade:
        list.insert(3, el)
    elif el[0].grade == list[3][0].grade and el[0].date >= list[3][0].date:
            list.insert(3, el)

    elif not list[4]:
        list[4]=el
    elif el[0].grade>list[4][0].grade and el[0].grade<=list[3][0].grade:
        list[4]=el
    elif el[0].grade==list[4][0].grade and el[0].date >= list[4][0].date:
            list[4] = el

    return list[:5]


@app.route('/')
def home():
    user = flask.request.args.get('user_id')
    if user:
        user = database.db.session.query(database.User).filter(database.User.id == user).first()

    recents = database.db.session.query(database.Book).order_by(database.Book.date.desc())[:50]
    best = database.db.session.query(database.Book).order_by(database.Book.grade.desc())[:50]
    r_author = {}
    b_author = {}
    r_list = {}
    b_list= {}
    for b in recents:
        r_author[b.author_id] = database.db.session.query(database.Author.complete_name).filter(database.Author.id == b.author_id).first()
        if user:
            r_list[b.id] = database.db.session.query(database.List).filter(and_(database.List.book_id == b.id, database.List.user_id==user.id, database.List.list_name!="notsaved")).first()
    for b in best:
        b_author[b.author_id] = database.db.session.query(database.Author.complete_name).filter(database.Author.id == b.author_id).first()
        r_list[b.id] = database.db.session.query(database.List).filter(and_(database.List.book_id == b.id, database.List.user_id == user.id, database.List.list_name != "notsaved")).first()
    return flask.render_template('home.html.jinja2', recents=recents, r_author =r_author , best=best, b_author=b_author, r_list=r_list, b_list=b_list, genres=genres, user=user)


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
    in_list=None
    if user:
        user = database.db.session.query(database.User).filter(database.User.id == user).first()
        in_list = database.db.session.query(database.List).filter(and_(database.List.book_id == book_id, database.List.user_id==user.id)).first()

    nb_grade = database.db.session.query(database.List).filter(and_(database.List.book_id==book_id, database.List.grade!=None)).count()
    book = database.db.session.query(database.Book).filter(database.Book.id == book_id).first()
    author = database.db.session.query(database.Author).filter(database.Author.id ==book.author_id).first()
    comments = (database.db.session.query(database.Comment, database.User).join(database.User, database.Comment.user_id==database.User.id).
                filter(and_(database.Comment.book_id == book_id, database.Comment.status==0)).order_by(database.Comment.date.desc()).all())
    return flask.render_template("book.html.jinja2", book=book, author=author, genres=genres, user=user, in_list=in_list, comments=comments, nb_grade=nb_grade)

@app.route('/search/<int:nr>', methods=["GET", "POST"])
def search(nr):
    user = flask.request.args.get('user_id')
    if user:
        user = database.db.session.query(database.User).filter(database.User.id == user).first()

    global cached_research
    query= flask.request.args.get('query')
    genre = flask.request.args.get('genre')
    grade = flask.request.args.get('grade')
    date = flask.request.args.get('date')
    quick = flask.request.args.get('quickSearch')

    if cached_research['query']!=query or cached_research['filters']!= {'genre': genre, 'date': date, 'grade': grade, 'quick':quick}:
        results, total = research_book(query, genre, grade, date, quick)
        cached_research={
            'query': query,
            'filters': {'genre': genre, 'date': date, 'grade': grade, 'quick':quick},
            'results': results,
            'total': total,
            'quick': ''
        }
    pages = cached_research['total']//60 + 1
    author={}
    blist={}
    for b in cached_research['results'][60*(nr-1):60*nr]:
        author[b.author_id] = database.db.session.query(database.Author.complete_name).filter(database.Author.id == b.author_id).first()
        if user:
            blist[b.id] = database.db.session.query(database.List).filter(and_(database.List.book_id == b.id, database.List.user_id == user.id, database.List.list_name != "notsaved")).first()

    return flask.render_template("search.html.jinja2", query=query, nr=nr, results=cached_research['results'][60*(nr-1):60*nr], total=cached_research['total'], pages=pages, author=author,
                                 blist=blist, genres=genres, genre=genre, date=date, grade=grade, quick=quick, user=user)

@app.route('/about/<int:user_id>')
def about(user_id):
    user = database.db.session.query(database.User).filter(database.User.id == user_id).first()
    book_list = database.db.session.query(database.List, database.Book).join(database.List, database.Book.id==database.List.book_id).filter(database.List.user_id == user_id).all()
    nb_books = len(book_list)
    grade = []
    for el in book_list:
        if el[0].grade: grade.append(el[0].grade)
    nb_grade = len(grade)
    average_grade = sum(grade)/len(grade)
    comments = database.db.session.query(database.Comment).filter(database.Comment.user_id == user_id).count()

    fav_genre = {}
    fav_books = [None] * 5
    if nb_books != 0:

        for genre in genres:
            c = 0
            for el in book_list:
                book_genres = el[1].genres.split(';')
                l = len(book_genres)
                print(book_genres)
                for i in range(l-1):
                    if book_genres[i]==genre:
                        c+= l-i
            fav_genre[genre]= c
        print(fav_genre)
        fav_genre = list(dict(sorted(fav_genre.items(), key=lambda item: item[1], reverse=True)))[:3]
        for el in book_list:
            has_genre=False
            for g in fav_genre:
                if g in el[1].genres.split(';'):
                    has_genre = True
                    break
            if has_genre:
                fav_books = find_fav_books(el, fav_books, nb_books)

    return flask.render_template("about.html.jinja2", user=user, genres=genres, fav_genre = fav_genre, fav_books=fav_books,
                                                                        nb_books=nb_books, nb_grade=nb_grade, average_grade=average_grade, comments=comments)

@app.route('/list/<int:user_id>')
def book_list(user_id):
    user = database.db.session.query(database.User).filter(database.User.id==user_id).first()
    order = flask.request.args.get('order')
    type = flask.request.args.get('type')
    books = (database.db.session.query(database.List, database.Book).
             join(database.List, database.Book.id==database.List.book_id).
             filter(database.List.user_id==user.id))
    if order=='desc':
        if type=='grade':
            books = books.order_by(database.List.grade, database.List.date).all()
        elif type=='title':
            books = books.order_by(database.Book.title.desc(), database.List.date).all()
        else:
            books = books.order_by(database.List.date).all()
    else:
        if type=='grade':
            books = books.order_by(database.List.grade.desc(), database.List.date.desc()).all()
        elif type=='title':
            books = books.order_by(database.Book.title, database.List.date.desc()).all()
        else:
            books = books.order_by(database.List.date.desc()).all()

    return flask.render_template("list.html.jinja2", user=user, genres=genres, books=books, order=order, type=type)

@app.route('/deleteAcount/<string:user_id>')
def deleteAccount(user_id):
    if user_id:
        user_id = int(user_id)
        database.delete_user(user_id)
    return {'message': 'User deleted'}

@app.route('/save', methods=['POST'])
def save():
    data = flask.request.json
    user_id = data.get('user_id')
    book_id = data.get('book_id')
    command = data.get('command')
    if user_id and book_id:
        user_id = int(user_id)
        book_id = int(book_id)
        if command=="add":
            database.add_book_to_list(book_id, user_id)
        else:
            database.remove_book_from_list(book_id, user_id)
    return {'message': 'save changed'}, 200

@app.route('/deleteComment', methods=['POST'])
def deleteComment():
    data = flask.request.json
    comment_id = data.get('comment_id')
    if comment_id:
        comment_id = int(comment_id)
        database.delete_comment(comment_id)
    return {'message': 'save changed'}, 200

@app.route('/addComment', methods=['POST'])
def addComment():
    data = flask.request.json
    user_id = data.get('user_id')
    book_id = data.get('book_id')
    content = data.get('content')
    if user_id and book_id:
        database.add_comment(int(user_id), int(book_id), str(content))

    return {'message': 'save changed'}, 200

@app.route('/addGrade', methods=['POST'])
def addGrade():
    data = flask.request.json
    user_id = data.get('user_id')
    book_id = data.get('book_id')
    grade = data.get('grade')
    if user_id and book_id:
        database.add_grade(int(user_id), int(book_id), int(grade))

    return {'message': 'save changed'}, 200




if __name__ == '__main__':
    app.run()

