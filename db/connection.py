from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.orm import *
#from dotenv import load_dotenv
import os

#load_dotenv()

#DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine("sqlite+pysqlite:///:memory:")
Session = sessionmaker(bind=engine)
session = Session()
Base.metadata.create_all(engine)