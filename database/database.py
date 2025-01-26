from flask_sqlalchemy import SQLAlchemy
from flask import url_for
import json
import random
from datetime import datetime, timedelta, date
from sqlalchemy import Index, func, update, select, and_
import psycopg2


db = SQLAlchemy()

def init_database():
    db.create_all()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text)
    email = db.Column(db.Text)
    password = db.Column(db.Text)
    date = db.Column(db.Date)


class Author(db.Model):
    __tablename__= 'authors'
    id = db.Column(db.Integer, primary_key = True)
    complete_name = db.Column(db.Text)
    last_name = db.Column(db.Text)
    first_name = db.Column(db.Text)
    nr_book = db.Column(db.Integer)

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key = True)
    isbn = db.Column(db.Integer)
    title = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'))
    date = db.Column(db.Date)
    synopsis = db.Column(db.Text)
    img_path = db.Column(db.Text)
    grade = db.Column(db.Float(10,3))
    genres = db.Column(db.Text)
    shelves = db.Column(db.Text)
    similar = db.Column(db.Text)

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
    content = db.Column(db.Text)
    status = db.Column(db.Integer) #0 for public comment, 1 for personnal note
    date = db.Column(db.Date)

class List(db.Model):
    __tablename__ = 'lists'
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
    list_name = db.Column(db.Text)
    grade = db.Column(db.Float(10,3))
    date = db.Column(db.Date)
    is_read = db.Column(db.Boolean)


def peupler():
    try:
        # Connexion à la base PostgreSQL
        conn = psycopg2.connect(
            "postgresql://bookhaven_qxlx_user:iim0rXsw1OJVy4efmBLECKbG59U1yeI9@dpg-cuaqottumphs73cn4r7g-a/bookhaven_qxlx"
        )
        cursor = conn.cursor()

        # Lire le contenu du fichier SQL
        with open('/postgresql_dump.sql', 'r') as f:
            sql = f.read()

        # Exécuter le SQL
        cursor.execute(sql)
        conn.commit()

        print("Fichier SQL exécuté avec succès.")

    except Exception as e:
        print(f"Erreur lors de l'exécution du fichier SQL : {e}")

    finally:
        # Fermer la connexion
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def new_user(username, password, mail):
    user = User(username=username, password=password, email=mail)
    db.session.add(user)
    db.session.commit()

def delete_user(id):
    db.session.query(List).filter(List.user_id==id).delete()
    db.session.query(Comment).filter(Comment.user_id==id).delete()
    db.session.query(User).filter(User.id==id).delete()
    db.session.commit()

def add_book_to_list(book_id, user_id):
    book_list = db.session.query(List).filter(and_(List.book_id==book_id, List.user_id==user_id, List.list_name==None)).first()
    if book_list:
        book_list.list_name = "My books"
        book_list.date = date.today()
        db.session.commit()
    else:
        list = List(user_id=user_id, book_id=book_id, list_name="My books", date=date.today(), is_read=False)
        db.session.add(list)
        db.session.commit()

def remove_book_from_list(book_id, user_id):
    book_list = db.session.query(List).filter(and_(List.book_id==book_id, List.user_id==user_id)).first()
    if book_list.grade:
        book_list.list_name = None
        book_list.date = None
        db.session.commit()
    else:
        db.session.delete(book_list)
        db.session.commit()



def add_grade(user_id, book_id, grade):
    book_list = db.session.query(List).filter(and_(List.book_id==book_id, List.user_id==user_id)).first()
    if book_list:
        book_list.grade = grade
        db.session.commit()
    else:
        list = List(user_id=user_id, book_id=book_id, grade=grade, date=date.today(), is_read=False)
        db.session.add(list)
        db.session.commit()



def mark_as_read(book_id, user_id):
    book_list = db.session.query(List).filter(and_(List.book_id==book_id, List.user_id==user_id)).first()
    if book_list:
        book_list.is_read = True
        db.session.commit()
    else:
        list = List(user_id=user_id, book_id=book_id, date=date.today(), is_read=True)
        db.session.add(list)
        db.session.commit()

def unmark_as_read(book_id, user_id):
    book_list = db.session.query(List).filter(and_(List.book_id == book_id, List.user_id == user_id)).first()
    if book_list.grade or book_list.list_name:
        book_list.is_read = False
        db.session.commit()
    else:
        db.session.delete(book_list)
        db.session.commit()


def add_comment(user_id, book_id, content):
    comment = Comment(user_id=user_id, book_id=book_id, content=content, status=0, date=date.today())
    db.session.add(comment)
    db.session.commit()


def delete_comment(comment_id):
    db.session.query(Comment).filter(Comment.id == comment_id).delete()
    db.session.commit()




def list_genres():
    genres=[]
    books =db.session.query(Book).all()
    for b in books:
        bgenre = b.genres.split(";")
        for g in bgenre:
            if g not in genres and g!='':
                genres.append(g)
    return(genres)



































def replace_no_cover():
    books = Book.query.all()
    img_name = db.session.query(Book.img_path).filter(Book.title == "Fugly").first()
    print(url_for('static', filename='img/no_cover.jfif'))
    print(img_name[0])
    for b in books:
        if b.img_path == img_name[0]:
            b.img_path = url_for('static', filename='img/no_cover.jfif')
    db.session.commit()

def add_book_genres():
    ids = db.session.query(Book.id).all()
    for id in ids:
        with open("./jsons/goodreads_book_genres_initial.json") as file:
            for line in file:
                data = json.loads(line)
                if data['book_id'] == str(id[0]):
                    book = db.session.query(Book).filter_by(id=data["book_id"]).first()
                    genre = ''
                    for g in data["genres"].keys():
                        genre += g + ";"
                    book.genres = genre
                    break
    db.session.commit()

def add_book_shelves():
    ids = db.session.query(Book.id).all()
    j=0
    for id in ids:
        with open("./jsons/goodreads_books.json") as file:
            for line in file:
                data = json.loads(line)
                if data['book_id'] == str(id[0]):
                    book = db.session.query(Book).filter_by(id=data["book_id"]).first()
                    shelves = {}
                    book_shelves = ''
                    for s in data["popular_shelves"]:
                        if 'read' not in s["name"] and 'own' not in s['name']:
                            shelves[s["name"]] = int(s["count"])
                    shelves = dict(sorted(shelves.items(), key=lambda item: item [1]))
                    i = 0
                    nb = 0
                    for el in shelves.items():
                        book_shelves += el[0] + ':'
                        if el[1] > nb:
                            nb = el[1]
                            i += 1
                        book_shelves += str(i) + ';'
                    book.shelves = book_shelves[:-1]
                    break
        j+=1
        print(j)
    db.session.commit()

def add_sim_book():
    books = db.session.query(Book).all()
    print(len(books))
    j = 0
    for b in books:
        j += 1
        print(j)
        if not b.shelves:
            continue
        book_shelves = {s.split(':')[0]:s.split(':')[1] for s in b.shelves.split(';')}
        sim = {}
        book_sim = ''
        nb=0
        for b2 in books:
            if b2.id != b.id:
                if b2.genres!='' and b.genres!='':
                    common = False
                    for g in b2.genres.split(';')[:-1]:
                        if g!="fiction" and g in b.genres:
                            common=True
                            nb+=1
                            break
                else: common = True

                if common:
                    match = 0
                    if b2.shelves!='':
                        for s in b2.shelves.split(';'):
                            if s.split(':')[0] in book_shelves.keys():
                                match += int(book_shelves[s.split(':')[0]]) + int(s.split(':')[1])
                    sim[b2.id] = match
        sim = dict(sorted(sim.items(), key=lambda item: item [1], reverse=True))
        i=0
        for el in sim.keys():
            book_sim += str(el) + ';'
            i+=1
            if i==30:
                break
        b.similar = book_sim[:-1]
        print('yes')

    db.session.commit()






def add_users():
    with open("./jsons/nom.json") as file:
        for line in file:
            data = json.loads(line)
            for name in data['name']:
                nom = name
                email = name.lower() + '@gmail.com'
                password = "password"
                user = User(username=nom, email=email, password=password)
                db.session.add(user)
    db.session.commit()




def add_books_to_lists():
    users = db.session.query(User).all()
    for u in users:
        books = db.session.query(Book).order_by(func.rand()).limit(500)
        for b in books:
            user = u.id
            book = b.id
            grade = random.randint(1,5)
            name = "My books"
            list = List(user_id=user, book_id=book, list_name=name, grade=grade)
            db.session.add(list)
    db.session.commit()

def update_grade():
    books=db.session.query(Book).all()
    lists = db.session.query(List).all()
    for book in books:
        grade=0
        nb=0
        for l in lists:
            if l.book_id == book.id:
                grade += l.grade
                nb+=1
        if nb!=0:
            book.grade = grade/nb
    db.session.commit()

def add_user_date():
    start = date(2020, 1, 1)
    end = date(2021,12,31)
    diff = (end-start).days
    users = db.session.query(User).all()
    for u in users:
        day=random.randint(1,diff)
        u.date=start+timedelta(days=day)
    db.session.commit()


def add_book_date():
    list = db.session.query(List, User,Book).join(Book, List.book_id==Book.id).join(User, List.user_id==User.id).all()
    for el in list:
        if el[2].date: start = max(el[1].date,el[2].date)
        else: start = el[1].date
        end = date.today()
        diff = (end-start).days
        day = random.randint(1,diff)
        el[0].date=start+timedelta(days=day)
    db.session.commit()

def add_comment_date():
    comment = db.session.query(Comment, User,Book).join(Book, Comment.book_id==Book.id).join(User, Comment.user_id==User.id).all()
    for el in comment:
        if el[2].date: start = max(el[1].date,el[2].date)
        else: start = el[1].date
        end = date.today()
        diff = (end-start).days
        day = random.randint(1,diff)
        el[0].date=start+timedelta(days=day)
    db.session.commit()

def add_comments():
    books = db.session.query(Book).all()
    users = db.session.query(User).all()
    nbuser = len(users)-1
    with open("./jsons/Critical_Reviews.json") as file:
        for line in file:
            data = json.loads(line)
            nbcomm = len(data["comments"])-1
            for b in books:
                lcomm = []
                lu = []
                for i in range(random.randint(5,10)):
                    bid = b.id
                    randu = random.randint(1, nbuser)
                    randcomm = random.randint(1, nbcomm)

                    while randu in lu:
                        randu = random.randint(1, nbuser)
                    while randcomm in lcomm:
                        randcomm = random.randint(1, nbcomm)
                    uid = users[randu].id
                    content = data['comments'][randcomm]

                    lu.append(randu)
                    lcomm.append(randcomm)

                    comment =Comment(user_id=uid, book_id=bid, content=content, status=0)
                    db.session.add(comment)
                print('book ', b, ' done')
    db.session.commit()

def delelete_author():
    authors = db.session.query(Author).all()
    for a in authors:
        if a.nr_book==0:
            db.session.delete(a)
    db.session.commit()

def add_read():
    users = db.session.query(User).all()
    for u in users:
        books = db.session.query(List).filter(List.user_id==u.id).all()
        print(len(books))
        if len(books)>50:
            nr = random.randint(50,len(books))
        else: nr= 0
        i=0
        for b in books:
            if i<nr:
                b.is_read = True
            else:
                b.is_read = False
            i+=1
    db.session.commit()
