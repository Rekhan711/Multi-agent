from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Sales(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    product = Column(String(100), nullable=False)
    region = Column(String(50), nullable=False)
    revenue = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    stock = Column(Integer, nullable=False)
    value = Column(Float, nullable=False)

class Finance(Base):
    __tablename__ = "finance"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    revenue = Column(Float, nullable=False)
    expense = Column(Float, nullable=False)
    profit = Column(Float, nullable=False)

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    department = Column(String(100), nullable=False)
    hire_date = Column(Date, nullable=False)
    termination_date = Column(Date, nullable=True)
    salary = Column(Float, nullable=False)
