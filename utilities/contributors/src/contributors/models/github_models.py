from pydantic import BaseModel


class GhOwner(BaseModel):
    login: str


class GhRepository(BaseModel):
    name: str
    owner: GhOwner
    full_name: str


class GhCommitAuthor(BaseModel):
    name: str


class GhCommit(BaseModel):
    author: GhCommitAuthor


class GhAuthor(BaseModel):
    login: str | None


class GhCommit(BaseModel):
    commit: GhCommit
    author: GhAuthor | None
