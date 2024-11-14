from app import db
from flask_login import UserMixin

class DIM_Band(db.Model):
    __tablename__ = 'DIM_Band'
    band_id = db.Column("band_id", db.BigInteger, primary_key=True)
    url = db.Column("url", db.Text, nullable=True)
    name = db.Column("name", db.Text, nullable=True)
    country = db.Column("country", db.Text, nullable=True)
    genre = db.Column("genre", db.Text, nullable=True)

class DIM_Discography(db.Model):
    __tablename__ = 'DIM_Discography'
    band_id = db.Column("band_id", db.BigInteger, db.ForeignKey('DIM_Band.band_id'), primary_key=True, nullable=False)
    name = db.Column("name", db.Text, primary_key=True, nullable=False)
    type = db.Column("type", db.Text, primary_key=True, nullable=False)
    year = db.Column("year", db.Integer, primary_key=True, nullable=False)
    reviews = db.Column("reviews", db.Text, nullable=True)

class DIM_Similar_Band(db.Model):
    __tablename__ = 'DIM_Similar_Band'
    band_id = db.Column("band_id", db.BigInteger, db.ForeignKey('DIM_Band.band_id'), primary_key=True, nullable=False)
    similar_id = db.Column("similar_id", db.BigInteger, db.ForeignKey('DIM_Band.band_id'), primary_key=True, nullable=False)
    score = db.Column("Score", db.Integer, nullable=True)

class DIM_Details(db.Model):
    __tablename__ = 'DIM_Details'
    band_id = db.Column("band_id", db.BigInteger, db.ForeignKey('DIM_Band.band_id'), primary_key=True, nullable=False)
    country = db.Column("country", db.Text, nullable=True)
    location = db.Column("location", db.Text, nullable=True)
    status = db.Column("status", db.Text, nullable=True)
    year_formed = db.Column("year_formed", db.Text, nullable=True)
    genre = db.Column("genre", db.Text, nullable=True)
    themes = db.Column("themes", db.Text, nullable=True)
    label = db.Column("label", db.Text, nullable=True)
    years_active = db.Column("years_active", db.Text, nullable=True)

class DIM_Member(db.Model):
    __tablename__ = 'DIM_Member'
    band_id = db.Column("band ID", db.BigInteger, db.ForeignKey('DIM_Band.band_id'), primary_key=True, nullable=False)
    member_id = db.Column("member ID", db.BigInteger, primary_key=True, nullable=False)
    name = db.Column("name", db.Text, nullable=True)
    role = db.Column("role", db.Text, nullable=True)
    category = db.Column("category", db.Text, nullable=False)

class users(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    Birthyear = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    nationality = db.Column(db.String(50), nullable=False)
    genre1 = db.Column(db.String(50), nullable=False)
    genre2 = db.Column(db.String(50), nullable=False)
    genre3 = db.Column(db.String(50), nullable=False)

class UserBandPreference(db.Model):
    __tablename__ = 'user_band_preference'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    band_id = db.Column(db.BigInteger, primary_key=True)
    liked = db.Column(db.Boolean, nullable=True)
    remind_me = db.Column(db.Boolean, nullable=True)

class DIM_Genre(db.Model):
    __tablename__ = 'DIM_genre'
    genre_id = db.Column("id", db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column("name", db.Text, unique=True, nullable=False)
    type = db.Column("type", db.String(10), nullable=False)

class DIM_Prefix(db.Model):
    __tablename__ = 'DIM_prefix'
    prefix_id = db.Column("id", db.Integer, primary_key=True, autoincrement=True)
    name = db.Column("name", db.Text, unique=True, nullable=False)
    type = db.Column("type", db.String(10), nullable=False)

class Bandgenre(db.Model):
    __tablename__ = 'Bandgenre'
    bridge_id = db.Column("bridge_id", db.BigInteger, primary_key=True, autoincrement=True)
    band_id = db.Column("band_id", db.BigInteger, db.ForeignKey('DIM_Band.band_id'), nullable=False)
    item_id = db.Column("item_id", db.Integer, nullable=False)
    type = db.Column("type", db.String(10), nullable=False)

class Bandtheme(db.Model):
    __tablename__ = 'Bandtheme'
    bridge_id = db.Column("bridge_id", db.BigInteger, primary_key=True, autoincrement=True)
    band_id = db.Column("band_id", db.BigInteger, db.ForeignKey('DIM_Band.band_id'), nullable=False)
    theme_id = db.Column("theme_id", db.Integer, db.ForeignKey('DIM_Theme.theme_id'), nullable=False)

class DIM_Theme(db.Model):
    __tablename__ = 'DIM_Theme'
    theme_id = db.Column("theme_id", db.Integer, primary_key=True, nullable=False)
    name = db.Column('name', db.Text, unique=True, nullable=False)