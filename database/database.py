from flask_sqlalchemy import SQLAlchemy
from flask import url_for
import json
from datetime import datetime
from sqlalchemy import Index, func, update


db = SQLAlchemy()

def init_database():
    db.create_all()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text)
    email = db.Column(db.Text)
    password = db.Column(db.Text)


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
    date = db.Column(db.DateTime)
    synopsis = db.Column(db.Text)
    img_path = db.Column(db.Text)
    grade = db.Column(db.Float(10,3))

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


def new_user(username, password, mail):
    user = User(username=username, password=password, email=mail)
    db.session.add(user)
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
