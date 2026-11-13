
from datetime import datetime
from typing import Annotated

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ConfigDict,
    BeforeValidator,
)


def validate_demo_email(value):
    if isinstance(value, str):
        value = value.strip()
        if value.lower().endswith(".local"):
            local_part, separator, domain = value.rpartition("@")
            if separator and local_part and domain:
                return value
    return str(EmailStr(value))


DemoEmail = Annotated[str, BeforeValidator(validate_demo_email)]


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: DemoEmail
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: DemoEmail
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class SkillIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: str = "Technical"
    self_rating: int = Field(default=3, ge=1, le=5)
    target_rating: int = Field(default=4, ge=1, le=5)


class SkillOut(BaseModel):
    id: int
    name: str
    category: str
    self_rating: int
    target_rating: int
    health: float | None = None
    status: str = "Insufficient Data"
    model_config = ConfigDict(from_attributes=True)


class ActivityIn(BaseModel):
    skill_id: int
    title: str = Field(min_length=1, max_length=180)
    description: str = ""
    activity_type: str = "Practice"
    duration_minutes: int = Field(default=30, ge=1, le=1440)
    difficulty: str = "Intermediate"
    score: float | None = Field(default=None, ge=0, le=100)


class EvidenceIn(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    evidence_type: str = "Project"
    description: str = ""
    url: str = ""
    skill_ids: list[int] = []


class AssessmentSubmit(BaseModel):
    answers: dict[int, int]


class JobAnalyzeIn(BaseModel):
    title: str = "Target role"
    description: str = Field(min_length=10, max_length=30000)


class ProfileIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class AIQuizGenerateIn(BaseModel):
    skill_id: int
    topic: str = Field(default="", max_length=120)
    difficulty: str = Field(default="Intermediate", max_length=30)
    count: int = Field(default=5, ge=3, le=10)


class AIQuizSubmitIn(BaseModel):
    quiz_id: str = Field(min_length=1, max_length=100)
    answers: dict[int, int] = Field(min_length=1, max_length=10)


