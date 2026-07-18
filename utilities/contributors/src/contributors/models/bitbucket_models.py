from pydantic import BaseModel
from typing import Optional

from contributors.models.reports import BaseReport


class BbUser(BaseModel):
    display_name: str


class BbAuthor(BaseModel):
    raw: str
    user: Optional[BbUser] = None


class BbRepository(BaseModel):
    name: str
    full_name: str


class BbCommit(BaseModel):
    date: str
    author: BbAuthor
