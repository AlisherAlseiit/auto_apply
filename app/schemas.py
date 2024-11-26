from datetime import datetime

from pydantic import BaseModel


class VacancyCreate(BaseModel):
    name: str
    link: str
    start: str