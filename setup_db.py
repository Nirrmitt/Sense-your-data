import os

from dotenv import load_dotenv
from sqlalchemy import Column, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base

load_dotenv()
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL is not configured.")

engine = create_engine(database_url, pool_pre_ping=True)
Base = declarative_base()

class Products(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    category = Column(String(100))
    price = Column(Float)

class Sales(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer)
    quantity = Column(Integer)
    date = Column(String(50))

Base.metadata.create_all(bind=engine)
print("Database Schema Created Successfully.")
