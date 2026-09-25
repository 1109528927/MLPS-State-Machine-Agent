from pydantic import BaseModel


class GapActionRequest(BaseModel):
    action: str
    comment: str | None = None


class GapCreateRequest(BaseModel):
    project_id: int
    title: str
    category: str | None = None
    risk_level: str | None = None
    reason: str | None = None
    requirement: str | None = None

