from sqlalchemy import Column, String, Integer
from fastapi_users.db import SQLAlchemyBaseUserTable
from database import Base


class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(String, default="user")
