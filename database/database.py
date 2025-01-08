from flask_sqlalchemy import SQLAlchemy
from flask import url_for
import json
import random
from datetime import datetime, timedelta, date
from sqlalchemy import Index, func, update, select


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

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
    content = db.Column(db.Text)
    status = db.Column(db.Integer)

class List(db.Model):
    __tablename__ = 'lists'
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
    list_name = db.Column(db.Text)
    grade = db.Column(db.Float(10,3))
    date = db.Column(db.Date)


def new_user(username, password, mail):
    user = User(username=username, password=password, email=mail)
    db.session.add(user)
    db.session.commit()

def delete_user(id):
    db.session.query(List).filter(List.user_id==id).delete()
    db.session.query(Comment).filter(Comment.user_id==id).delete()
    db.session.query(User).filter(User.id==id).delete()
    db.session.commit()

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
    i = 0
    for id in ids:
        i+=1
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
        print(i)
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




def list_genres():
    genres=[]
    books =db.session.query(Book).all()
    for b in books:
        bgenre = b.genres.split(";")
        for g in bgenre:
            if g not in genres and g!='':
                genres.append(g)
    return(genres)

def add_book_to_list():
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