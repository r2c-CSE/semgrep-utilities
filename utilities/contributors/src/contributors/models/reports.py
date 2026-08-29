from pydantic import BaseModel


class RepositoryStats(BaseModel):
    name: str
    contributor_count: int
    contributors: list[str]


class BaseReport(BaseModel):
    date: str
    number_of_days_history: int
    repository_stats: list[RepositoryStats]
    total_contributor_count: int
    total_repository_count: int


class AdoReport(BaseReport):
    organization: str
    all_contributor_emails: list[str]


class BbReport(BaseReport):
    workspace: str
    all_contributors: list[str]


class GlReport(BaseReport):
    all_contributors: list[str]


class GhReport(BaseReport):
    organization: str
    org_members: list[str]
    org_contributors: list[str]
    org_contributors_count: int
