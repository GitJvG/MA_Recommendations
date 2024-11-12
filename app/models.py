from app import db
from flask_login import UserMixin

class DIM_Band(db.Model):
    __tablename__ = 'DIM_Band'
    Band_ID = db.Column("Band ID", db.BigInteger, primary_key=True)
    Band_URL = db.Column("Band URL", db.Text, nullable=True)
    Band_Name = db.Column("Band Name", db.Text, nullable=True)
    Country = db.Column("Country", db.Text, nullable=True)
    Genre = db.Column("Genre", db.Text, nullable=True)

class DIM_Discography(db.Model):
    __tablename__ = 'DIM_Discography'
    Band_ID = db.Column("Band ID", db.BigInteger, db.ForeignKey('DIM_Band.Band ID'), primary_key=True, nullable=False)
    Album_Name = db.Column("Album Name", db.Text, primary_key=True, nullable=False)
    Type = db.Column("Type", db.Text, primary_key=True, nullable=False)
    Year = db.Column("Year", db.Integer, primary_key=True, nullable=False)
    Reviews = db.Column("Reviews", db.Text, nullable=True)

class DIM_Similar_Band(db.Model):
    __tablename__ = 'DIM_Similar_Band'
    Band_ID = db.Column("Band ID", db.BigInteger, db.ForeignKey('DIM_Band.Band ID'), primary_key=True, nullable=False)
    Similar_Artist_ID = db.Column("Similar Artist ID", db.BigInteger, db.ForeignKey('DIM_Band.Band ID'), primary_key=True, nullable=False)
    Score = db.Column("Score", db.Integer, nullable=True)

class DIM_Details(db.Model):
    __tablename__ = 'DIM_Details'
    Band_ID = db.Column("Band ID", db.BigInteger, db.ForeignKey('DIM_Band.Band ID'), primary_key=True, nullable=False)
    Country_of_origin = db.Column("Country of origin", db.Text, nullable=True)
    Location = db.Column("Location", db.Text, nullable=True)
    Status = db.Column("Status", db.Text, nullable=True)
    Formed_in = db.Column("Formed in", db.Text, nullable=True)
    Genre = db.Column("Genre", db.Text, nullable=True)
    Themes = db.Column("Themes", db.Text, nullable=True)
    Current_label = db.Column("Current label", db.Text, nullable=True)
    Years_active = db.Column("Years active", db.Text, nullable=True)
    Last_label = db.Column("Last label", db.Text, nullable=True)

class DIM_Member(db.Model):
    __tablename__ = 'DIM_Member'
    Band_ID = db.Column("Band ID", db.BigInteger, db.ForeignKey('DIM_Band.Band ID'), primary_key=True, nullable=False)
    Member_ID = db.Column("Member ID", db.BigInteger, primary_key=True, nullable=False)
    Name = db.Column("Name", db.Text, nullable=True)
    Role = db.Column("Role", db.Text, nullable=True)
    Category = db.Column("Category", db.Text, nullable=False)

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

class Item(db.Model):
    __tablename__ = 'item'
    
    item = db.Column(db.BigInteger, primary_key=True)
    band_name = db.Column(db.Text, nullable=True)
    country = db.Column(db.Text, nullable=True)
    status = db.Column(db.Text, nullable=True)
    genre1 = db.Column(db.Text, nullable=True)
    genre2 = db.Column(db.Text, nullable=True)
    genre3 = db.Column(db.Text, nullable=True)
    genre4 = db.Column(db.Text, nullable=True)
    theme1 = db.Column(db.Text, nullable=True)
    theme2 = db.Column(db.Text, nullable=True)
    theme3 = db.Column(db.Text, nullable=True)
    theme4 = db.Column(db.Text, nullable=True)
    score = db.Column(db.Integer, nullable=True, index=True)

    """__table_args__ = (
        db.UniqueConstraint("item", name="unique_item_entry"),
    )"""

class UserCandidateRecommendation(db.Model):
    __tablename__ = 'user_candidate_recommendation'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, primary_key=True)
    item_id = db.Column(db.BigInteger, db.ForeignKey('item.item'), nullable=False, primary_key=True)

