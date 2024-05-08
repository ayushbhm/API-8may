from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Genre(db.Model):
    __tablename__ = 'Genre'
    name = db.Column(db.String, primary_key=True, nullable=False, unique=True)

class Movie(db.Model):
    __tablename__ = 'Movie'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer)
    imdb_rating = db.Column(db.Integer)



class MovieGenre(db.Model):
    __tablename__ = 'Moviegenre'
    movie_id = db.Column(db.Integer, db.ForeignKey('Movie.id'), primary_key=True)
    genre_name = db.Column(db.String, db.ForeignKey('Genre.name'), primary_key=True)



class Person(db.Model):
    __tablename__ = 'Person'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    personname = db.Column(db.String, nullable=False)


class Roles(db.Model):
    __tablename__ = 'Roles'
    name = db.Column(db.String, primary_key=True, nullable=False, unique=True)



class MoviePersonRole(db.Model):
    __tablename__ = 'Moviepersonrole'
    movie_id = db.Column(db.Integer, db.ForeignKey('Movie.id'), primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('Person.id'), primary_key=True)
    role_name = db.Column(db.String, db.ForeignKey('Roles.name'), primary_key=True)
    


    