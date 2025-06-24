from MA_Scraper.app import db
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from flask_login import UserMixin

class BandGenres(db.Model):
    __tablename__ = 'band_genres'
    band_id = db.Column(db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True)
    id = db.Column(db.Integer, db.ForeignKey('genre.id'), primary_key=True)

    band_obj = db.relationship('Band', viewonly=True)
    genre_item = db.relationship('Genre', viewonly=True)

class BandPrefixes(db.Model):
    __tablename__ = 'band_prefixes'
    band_id = db.Column(db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True)
    id = db.Column(db.Integer, db.ForeignKey('prefix.id'), primary_key=True)

    band_obj = db.relationship('Band', viewonly=True)
    prefix_item = db.relationship('Prefix', viewonly=True)

class Themes(db.Model):
    __tablename__ = 'themes'
    band_id = db.Column(db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True)
    theme_id = db.Column(db.Integer, db.ForeignKey('theme.theme_id'), primary_key=True)

    band = relationship('Band', viewonly=True)
    theme = relationship("Theme", viewonly=True)

class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True, nullable=False)

    bands = db.relationship('Band', secondary=BandGenres.__table__, back_populates='genres')

class Prefix(db.Model):
    __tablename__ = 'prefix'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True, nullable=False)

    bands = db.relationship('Band', secondary=BandPrefixes.__table__, back_populates='prefixes')

class Theme(db.Model):
    __tablename__ = 'theme'
    theme_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True, nullable=False)

    bands = db.relationship('Band', secondary=Themes.__table__, back_populates='themes')

class Band(db.Model):
    __tablename__ = 'band'
    band_id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.Text, nullable=True)
    country = db.Column(db.Text, nullable=True)
    genre = db.Column(db.Text, nullable=True)
    location = db.Column(db.Text, nullable=True)
    status = db.Column(db.Text, nullable=True)
    year_formed = db.Column(db.Integer, nullable=True)
    theme = db.Column('themes', db.Text, nullable=True)
    label = db.Column(db.Text, nullable=True)
    label_id = db.Column(db.Integer, db.ForeignKey('label.label_id'), nullable=True)
    years_active = db.Column(db.Text, nullable=True)

    discography_items = relationship("Discography", back_populates="band")
    members = relationship("Member", back_populates="band")
    logo = relationship("Band_logo", uselist=False, back_populates="band")
    band_label = relationship("Label", back_populates="band")

    user_interactions = relationship("Users", back_populates="band_obj")
    candidate_users_link = relationship("Candidates", back_populates="band_obj")
    outgoing_similarities  = relationship("Similar_band", foreign_keys="Similar_band.band_id", back_populates="source_band")
    incoming_similarities  = relationship("Similar_band", foreign_keys="Similar_band.similar_id", back_populates="similar_band")

    genres = db.relationship(Genre, secondary=BandGenres.__table__, back_populates='bands')
    prefixes = db.relationship(Prefix, secondary=BandPrefixes.__table__, back_populates='bands')
    themes = relationship(Theme, secondary=Themes.__table__, back_populates="bands")

class Discography(db.Model):
    __tablename__ = 'discography'
    band_id = db.Column(db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True, nullable=False)
    album_id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column( db.Text, nullable=False)
    type = db.Column(db.Text, nullable=True)
    year = db.Column(db.Integer, nullable=True)
    reviews = db.Column(db.Text, nullable=True)
    review_count = db.Column(db.Integer, nullable=True)
    review_score = db.Column(db.Integer, nullable=True)

    band = relationship(Band, back_populates="discography_items")

class Similar_band(db.Model):
    __tablename__ = 'similar_band'
    band_id = db.Column(db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True)
    similar_id = db.Column(db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True)
    score = db.Column(db.Integer, nullable=True)

    source_band = relationship(Band, foreign_keys=[band_id], back_populates="outgoing_similarities")
    similar_band = relationship(Band, foreign_keys=[similar_id], back_populates="incoming_similarities")

class Label(db.Model):
    __tablename__ = 'label'
    label_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    country = db.Column(db.Text, nullable=True)
    genre = db.Column(db.Text, nullable=True)
    status = db.Column(db.Text, nullable=True)

    band = relationship(Band, back_populates="band_label")

class Member(db.Model):
    __tablename__ = 'member'
    band_id = db.Column(db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True)
    member_id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    name = db.Column(db.Text, nullable=True)
    role = db.Column(db.Text, nullable=True)
    category = db.Column(db.Text, nullable=False)

    band = relationship(Band, back_populates="members")

class Band_logo(db.Model):
    __tablename__ = 'band_logo'
    band_id = db.Column(db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True)
    data = db.Column(db.LargeBinary, nullable=False)
    retrieved_at = db.Column(db.DateTime(timezone=True), default=func.now())
    content_type = db.Column(db.Text, nullable=False)

    band = relationship(Band, back_populates="logo")

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

    user_interactions = relationship("Users", back_populates="user")
    candidate_bands_link = relationship("Candidates", back_populates="user")

class Users(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    band_id = db.Column(db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True)
    liked = db.Column(db.Boolean, nullable=True)
    liked_date = db.Column(db.DateTime, nullable=True)
    remind_me = db.Column(db.Boolean, nullable=True)
    remind_me_date = db.Column(db.DateTime, nullable=True)

    user = relationship(User, back_populates="user_interactions")
    band_obj = relationship(Band, back_populates="user_interactions")

class User_albums(db.Model):
    __tablename__ = 'user_albums'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    band_id = db.Column(db.BigInteger, primary_key=True)
    album_id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Text, nullable=True)
    modified_date = db.Column(db.DateTime, nullable=True)
    creation_date = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.ForeignKeyConstraint(
            ['band_id', 'album_id'],
            ['discography.band_id', 'discography.album_id']),{})

class Candidates(db.Model):
    __tablename__ = 'candidates'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True, nullable=False)
    band_id = db.Column(db.BigInteger, db.ForeignKey('band.band_id'), primary_key=True, nullable=False)
    cluster_id = db.Column(db.Integer, nullable=False)

    user = relationship(User, back_populates="candidate_bands_link")
    band_obj = relationship(Band, back_populates="candidate_users_link")