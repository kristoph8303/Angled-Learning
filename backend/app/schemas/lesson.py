from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Competency(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    description: str = ""
    priority: float = Field(ge=0.0, le=1.0)
    source: list[Literal["onet", "employer", "certification", "manual"]] = ["manual"]


class CompetencyMap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_title: str = Field(min_length=1)
    onet_code: str | None = None
    competencies: list[Competency] = Field(min_length=1)
    target_hours: float = Field(gt=0)
    certification_targets: list[str] = Field(default_factory=list)


class ContentBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal[
        "text",
        "procedure",
        "warning",
        "example",
        "diagram",
        "code",
        "checklist",
    ]
    title: str | None = None
    body: str
    competency_ids: list[str] = Field(default_factory=list)


class AssessmentQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    question: str
    question_type: Literal["multiple_choice", "short_answer", "practical"]
    options: list[str] = Field(default_factory=list)
    correct_answer: str | None = None
    rubric: str | None = None


class Assessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    assessment_type: Literal["quiz", "practical"]
    instructions: str
    passing_score: float = Field(ge=0, le=100)
    questions: list[AssessmentQuestion] = Field(min_length=1)


class Lesson(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"

    id: UUID | None = None
    title: str
    summary: str
    estimated_minutes: int = Field(gt=0)

    competency_ids: list[str] = Field(min_length=1)

    learning_objectives: list[str] = Field(min_length=1)

    content_blocks: list[ContentBlock] = Field(min_length=1)

    assessment: Assessment

    instructor_notes: list[str] = Field(default_factory=list)
    student_materials: list[str] = Field(default_factory=list)
