from app import db
from flask_login import UserMixin

class band(db.Model):
    __tablename__ = 'band'
    band_id = db.Column("band_id", db.BigInteger, primary_key=True)
    name = db.Column("name", db.Text, nullable=True)
    country = db.Column("country", db.Text, nullable=True)
    genre = db.Column("genre", db.Text, nullable=True)

class discography(db.Model):
    __tablename__ = 'discography'
    band_id = db.Column("band_id", db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True, nullable=False)
    name = db.Column("name", db.Text, nullable=False)
    type = db.Column("type", db.Text, nullable=False)
    year = db.Column("year", db.Integer, nullable=False)
    reviews = db.Column("reviews", db.Text, nullable=True)
    review_count = db.Column("review_count", db.Integer, nullable=True)
    review_score = db.Column("review_score", db.Integer, nullable=True)
    album_id = db.Column('album_id', db.Integer, primary_key=True, nullable=False)

class similar_band(db.Model):
    __tablename__ = 'similar_band'
    band_id = db.Column("band_id", db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True, nullable=False)
    similar_id = db.Column("similar_id", db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True, nullable=False)
    score = db.Column("score", db.Integer, nullable=True)

class details(db.Model):
    __tablename__ = 'details'
    band_id = db.Column("band_id", db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True, nullable=False)
    country = db.Column("country", db.Text, nullable=True)
    location = db.Column("location", db.Text, nullable=True)
    status = db.Column("status", db.Text, nullable=True)
    year_formed = db.Column("year_formed", db.Integer, nullable=True)
    genre = db.Column("genre", db.Text, nullable=True)
    themes = db.Column("themes", db.Text, nullable=True)
    label = db.Column("label", db.Text, nullable=True)
    years_active = db.Column("years_active", db.Text, nullable=True)

class member(db.Model):
    __tablename__ = 'member'
    band_id = db.Column("band_id", db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True, nullable=False)
    member_id = db.Column("member_id", db.BigInteger, primary_key=True, nullable=False)
    name = db.Column("name", db.Text, nullable=True)
    role = db.Column("role", db.Text, nullable=True)
    category = db.Column("category", db.Text, nullable=False)

class user(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    birthyear = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    nationality = db.Column(db.String(50), nullable=False)
    genre1 = db.Column(db.String(50), nullable=False)
    genre2 = db.Column(db.String(50), nullable=False)
    genre3 = db.Column(db.String(50), nullable=False)

class users(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    band_id = db.Column(db.BigInteger, primary_key=True)
    liked = db.Column(db.Boolean, nullable=True)
    liked_date = db.Column(db.DateTime, nullable=True)
    remind_me = db.Column(db.Boolean, nullable=True)
    remind_me_date = db.Column(db.DateTime, nullable=True)

class genre(db.Model):
    __tablename__ = 'genre'
    genre_id = db.Column("id", db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column("name", db.Text, unique=True, nullable=False)
    type = db.Column("type", db.String(10), nullable=False)


class hgenre(db.Model):
    __tablename__ = 'hgenre'
    hgenre_id = db.Column("id", db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column("name", db.Text, unique=True, nullable=False)
    type = db.Column("type", db.String(15), nullable=False)

class prefix(db.Model):
    __tablename__ = 'prefix'
    prefix_id = db.Column("id", db.Integer, primary_key=True, autoincrement=True)
    name = db.Column("name", db.Text, unique=True, nullable=False)
    type = db.Column("type", db.String(10), nullable=False)

class genres(db.Model):
    __tablename__ = 'genres'
    bridge_id = db.Column("bridge_id", db.BigInteger, primary_key=True, autoincrement=True)
    band_id = db.Column("band_id", db.BigInteger, db.ForeignKey('band.band_id'), nullable=False)
    item_id = db.Column("item_id", db.Integer, nullable=False)
    type = db.Column("type", db.String(15), nullable=False)

class themes(db.Model):
    __tablename__ = 'themes'
    bridge_id = db.Column("bridge_id", db.BigInteger, primary_key=True, autoincrement=True)
    band_id = db.Column("band_id", db.BigInteger, db.ForeignKey('band.band_id'), nullable=False)
    theme_id = db.Column("theme_id", db.Integer, db.ForeignKey('theme.theme_id'), nullable=False)

class theme(db.Model):
    __tablename__ = 'theme'
    theme_id = db.Column("theme_id", db.Integer, primary_key=True, nullable=False)
    name = db.Column('name', db.Text, unique=True, nullable=False)

class candidates(db.Model):
    __tablename__ = 'candidates'
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True, nullable=False)
    band_id = db.Column('band_id', db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True, nullable=False)

class label(db.Model):
    __tablename__ = 'label'
    label_id = db.Column('label_id', db.BigInteger, primary_key=True, nullable=False)
    name = db.Column('name', db.Text, nullable=False)
    country = db.Column('country', db.Text, nullable=True)
    genre = db.Column('genre', db.Text, nullable=True)
    status = db.Column('status', db.Text, nullable=True)