from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, text, ForeignKey, Table

from .database import Base


class Vacancy(Base):
    __tablename__ = "vacancies"

    email = Column(String, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    link = Column(String, nullable=False)
    start = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    