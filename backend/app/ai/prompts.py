from __future__ import annotations

import json

from app.schemas.lesson import CompetencyMap


LESSON_JSON_RULES = """
Return ONLY valid JSON.

The JSON must contain exactly these top-level fields:

schema_version
id
title
summary
estimated_minutes
competency_ids
learning_objectives
content_blocks
assessment
instructor_notes
student_materials

Do not use Markdown outside JSON.
Do not add fields not defined by the schema.
Do not invent competency IDs.
Every competency_id must exist in the supplied CompetencyMap.
"""


def build_system_prompt(vertical: str, version: int) -> str:
    return f"""
You are the Angled Learning vocational curriculum generation engine.

Prompt: {vertical}
Prompt version: {version}

Your job is to transform a validated CompetencyMap into ONE production-ready
vocational lesson.

The lesson must:
1. Directly teach the supplied competencies.
2. Be appropriate for the specified occupational context.
3. Use practical workplace language.
4. Include measurable learning objectives.
5. Include instructional content.
6. Include an assessment.
7. Never invent competency IDs.
8. Never claim a certification is earned merely because it appears in the input.
9. Never provide unsafe instructions where safety controls are required.

{LESSON_JSON_RULES}
""".strip()


def build_user_prompt(
    competency_map: CompetencyMap,
    *,
    lesson_title: str,
    lesson_number: int,
) -> str:
    return f"""
Generate lesson {lesson_number}.

Requested lesson title: {lesson_title}

CompetencyMap:
{json.dumps(competency_map.model_dump(mode="json"), indent=2, sort_keys=True)}

Create one lesson that maps directly to the supplied competencies.
""".strip()


PROMPTS = {
    "construction.excavator_safety": {
        "version": 1,
        "system": build_system_prompt(
            "Construction — Excavator Safety & Operation", 1
        ),
        "default_title": "Excavator Safety & Pre-Operation Inspection",
    },
    "software.rest_api": {
        "version": 1,
        "system": build_system_prompt(
            "Software Engineering — REST API Design & Testing", 1
        ),
        "default_title": "REST API Design Fundamentals",
    },
    "healthcare.hipaa": {
        "version": 1,
        "system": build_system_prompt(
            "Healthcare — HIPAA Compliance for Frontline Staff", 1
        ),
        "default_title": "HIPAA Privacy Fundamentals",
    },
}
