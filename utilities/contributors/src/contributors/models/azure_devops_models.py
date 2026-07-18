from pydantic import BaseModel
from typing import Optional


class AdoProject(BaseModel):
    name: str
    id: str


class AdoRepository(BaseModel):
    name: str
    id: str


class AdoCommitAuthor(BaseModel):
    name: str
    email: str
    date: str
    display_name: Optional[str] = None


class AdoCommit(BaseModel):
    commitId: str
    author: AdoCommitAuthor
    committer: AdoCommitAuthor
