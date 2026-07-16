from pydantic import BaseModel, Field


class ProjectRecord(BaseModel):
    id: str
    name: str
    city: str
    location: str
    status: str
    typology: str
    pricing_from: str
    amenities: list[str] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
    education: str
    site_visit_note: str
    brochure_note: str


class ProjectSummary(BaseModel):
    id: str
    name: str
    city: str
    status: str
