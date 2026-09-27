from .business import validate_competency_references
from app.schemas.lesson import CompetencyMap, Lesson


def validate_competency_references(
    lesson: Lesson,
    competency_map: CompetencyMap,
) -> None:
    valid_ids = {competency.id for competency in competency_map.competencies}
    referenced = set(lesson.competency_ids)

    for block in lesson.content_blocks:
        referenced.update(block.competency_ids)

    unknown = referenced - valid_ids

    if unknown:
        raise ValueError(f"Lesson references unknown competencies: {unknown}")
