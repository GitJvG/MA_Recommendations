from MA_Scraper.app import db
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from flask_login import UserMixin

class BandGenres(db.Model):
    __tablename__ = 'band_genres'
    band_id = db.Column(db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True)
    id = db.Column(db.BigInteger, db.ForeignKey('genre.id'), primary_key=True)

    band_obj = db.relationship('band', viewonly=True)
    genre_item = db.relationship('genre', viewonly=True)

class BandHgenres(db.Model):
    __tablename__ = 'band_hgenres'
    band_id = db.Column(db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True)
    id = db.Column(db.BigInteger, db.ForeignKey('hgenre.id'), primary_key=True)

    band_obj = db.relationship('band', viewonly=True)
    hgenre_item = db.relationship('hgenre', viewonly=True)

class BandPrefixes(db.Model):
    __tablename__ = 'band_prefixes'
    band_id = db.Column(db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True)
    id = db.Column(db.Integer, db.ForeignKey('prefix.id'), primary_key=True)

    band_obj = db.relationship('band', viewonly=True)
    prefix_item = db.relationship('prefix', viewonly=True)

class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column("id", db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column("name", db.Text, unique=True, nullable=False)

    bands = db.relationship('band', secondary=BandGenres.__table__, back_populates='genres')

class Hgenre(db.Model):
    __tablename__ = 'hgenre'
    id = db.Column("id", db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column("name", db.Text, unique=True, nullable=False)

    bands = db.relationship('band', secondary=BandHgenres.__table__, back_populates='hgenres')

class Prefix(db.Model):
    __tablename__ = 'prefix'
    id = db.Column("id", db.Integer, primary_key=True, autoincrement=True)
    name = db.Column("name", db.Text, unique=True, nullable=False)

    bands = db.relationship('band', secondary=BandPrefixes.__table__, back_populates='prefixes')

class Band(db.Model):
    __tablename__ = 'band'
    band_id = db.Column("band_id", db.BigInteger, primary_key=True)
    name = db.Column("name", db.Text, nullable=True)
    country = db.Column("country", db.Text, nullable=True)
    genre = db.Column("genre", db.Text, nullable=True)

    discography_items = relationship("discography", back_populates="band")
    details = relationship("details", uselist=False, back_populates="band")
    members = relationship("member", back_populates="band")
    logo = relationship("band_logo", uselist=False, back_populates="band")

    theme_links = relationship("themes", back_populates="band")

    user_interactions = relationship("users", back_populates="band_obj")
    candidate_users_link = relationship("candidates", back_populates="band_obj")
    outgoing_similarities  = relationship("similar_band", foreign_keys="similar_band.band_id", back_populates="source_band")
    incoming_similarities  = relationship("similar_band", foreign_keys="similar_band.similar_id", back_populates="similar_band")

    genres = db.relationship('genre', secondary=BandGenres.__table__, back_populates='bands')
    hgenres = db.relationship('hgenre', secondary=BandHgenres.__table__, back_populates='bands')
    prefixes = db.relationship('prefix', secondary=BandPrefixes.__table__, back_populates='bands')

class Discography(db.Model):
    __tablename__ = 'discography'
    band_id = db.Column("band_id", db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True, nullable=False)
    album_id = db.Column('album_id', db.Integer, primary_key=True, nullable=False)
    name = db.Column("name", db.Text, nullable=False)
    type = db.Column("type", db.Text, nullable=True)
    year = db.Column("year", db.Integer, nullable=True)
    reviews = db.Column("reviews", db.Text, nullable=True)
    review_count = db.Column("review_count", db.Integer, nullable=True)
    review_score = db.Column("review_score", db.Integer, nullable=True)

    band = relationship("band", back_populates="discography_items")

class Similar_band(db.Model):
    __tablename__ = 'similar_band'
    band_id = db.Column("band_id", db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True, nullable=False)
    similar_id = db.Column("similar_id", db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True, nullable=False)
    score = db.Column("score", db.Integer, nullable=True)

    source_band = relationship("band", foreign_keys=[band_id], back_populates="outgoing_similarities")
    similar_band = relationship("band", foreign_keys=[similar_id], back_populates="incoming_similarities")

class Label(db.Model):
    __tablename__ = 'label'
    label_id = db.Column('label_id', db.BigInteger, primary_key=True, nullable=False)
    name = db.Column('name', db.Text, nullable=False)
    country = db.Column('country', db.Text, nullable=True)
    genre = db.Column('genre', db.Text, nullable=True)
    status = db.Column('status', db.Text, nullable=True)

class Details(db.Model):
    # Label isn't a foreign key yet because of label scraping issues for special characters.
    __tablename__ = 'details'
    band_id = db.Column("band_id", db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True, nullable=False)
    country = db.Column("country", db.Text, nullable=True)
    location = db.Column("location", db.Text, nullable=True)
    status = db.Column("status", db.Text, nullable=True)
    year_formed = db.Column("year_formed", db.Integer, nullable=True)
    genre = db.Column("genre", db.Text, nullable=True)
    themes = db.Column("themes", db.Text, nullable=True)
    label = db.Column("label", db.Text, nullable=True)
    label_id = db.Column("label_id", db.BigInteger, nullable=True)
    years_active = db.Column("years_active", db.Text, nullable=True)

    band = relationship("band", back_populates="details")

class Member(db.Model):
    __tablename__ = 'member'
    band_id = db.Column("band_id", db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True, nullable=False)
    member_id = db.Column("member_id", db.BigInteger, primary_key=True, nullable=False)
    name = db.Column("name", db.Text, nullable=True)
    role = db.Column("role", db.Text, nullable=True)
    category = db.Column("category", db.Text, nullable=False)

    band = relationship("band", back_populates="members")

class Band_logo(db.Model):
    __tablename__ = 'band_logo'
    band_id = db.Column('band_id', db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True, nullable=False)
    data = db.Column('data', db.LargeBinary, nullable=False)
    retrieved_at = db.Column('retrieved_at', db.DateTime(timezone=True), default=func.now())
    content_type = db.Column('content_type', db.String(50), nullable=False)

    band = relationship("band", back_populates="logo")

class User(db.Model, UserMixin):
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

    liked_bands_link = relationship("users", back_populates="user")
    candidate_bands_link = relationship("candidates", back_populates="user")

class Users(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    band_id = db.Column(db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True)
    liked = db.Column(db.Boolean, nullable=True)
    liked_date = db.Column(db.DateTime, nullable=True)
    remind_me = db.Column(db.Boolean, nullable=True)
    remind_me_date = db.Column(db.DateTime, nullable=True)

    user = relationship("user", back_populates="liked_bands_link")
    band_obj = relationship("band", back_populates="user_interactions")

class Themes(db.Model):
    __tablename__ = 'themes'
    bridge_id = db.Column("bridge_id", db.BigInteger, primary_key=True, autoincrement=True)
    band_id = db.Column("band_id", db.BigInteger, db.ForeignKey('band.band_id'), nullable=False)
    theme_id = db.Column("theme_id", db.Integer, db.ForeignKey('theme.theme_id'), nullable=False)

    band = relationship("band", back_populates="theme_links")
    theme = relationship("theme", back_populates="band_themes")

class Theme(db.Model):
    __tablename__ = 'theme'
    theme_id = db.Column("theme_id", db.Integer, primary_key=True, nullable=False)
    name = db.Column('name', db.Text, unique=True, nullable=False)

    band_themes = relationship("themes", back_populates="theme")

class Candidates(db.Model):
    __tablename__ = 'candidates'
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True, nullable=False)
    band_id = db.Column('band_id', db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True, nullable=False)

    user = relationship("user", back_populates="candidate_bands_link")
    band_obj = relationship("band", back_populates="candidate_users_link")