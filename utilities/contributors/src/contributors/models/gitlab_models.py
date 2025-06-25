from pydantic import BaseModel


class GlGroup(BaseModel):
    name: str
    id: int


class GlProject(BaseModel):
    path_with_namespace: str
    id: int
    name: str


class GlCommit(BaseModel):
    author_name: str
