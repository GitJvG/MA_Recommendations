from MA_Scraper.Env import load_config
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

engine = create_engine(load_config('SQL_Url'))
Session = scoped_session(sessionmaker(bind=engine))
