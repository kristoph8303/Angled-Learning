from __future__ import annotations

import asyncio
import hashlib
import json
import random
from dataclasses import dataclass

from pydantic import ValidationError

from app.ai.providers import AIProvider
from app.schemas.lesson import CompetencyMap, Lesson
from app.validation.business import validate_competency_references


MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 1.0


class LessonGenerationError(RuntimeError):
    pass


@dataclass(frozen=True)
class PromptVersion:
    name: str
    version: int
    template: str
    output_schema_name: str
    output_schema_version: str
    model_provider: str
    model_name: str


def calculate_cache_key(
    *, competency_map: CompetencyMap, prompt: PromptVersion, lesson_title: str
) -> str:
    payload = {
        "competency_map": competency_map.model_dump(mode="json"),
        "prompt_name": prompt.name,
        "prompt_version": prompt.version,
        "schema": prompt.output_schema_name,
        "schema_version": prompt.output_schema_version,
        "model_provider": prompt.model_provider,
        "model_name": prompt.model_name,
        "lesson_title": lesson_title,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"ai:lesson:{digest}"


def exponential_backoff(attempt: int) -> float:
    base = BASE_BACKOFF_SECONDS * (2 ** attempt)
    return base + random.uniform(0, 0.25)


async def retry_generate(
    provider: AIProvider,
    *,
    system_prompt: str,
    user_prompt: str,
    schema: dict,
    max_retries: int = MAX_RETRIES,
) -> str:
    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return await asyncio.to_thread(
                provider.generate,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema=schema,
            )
        except Exception as exc:
            last_error = exc
            if attempt >= max_retries:
                break
            await asyncio.sleep(exponential_backoff(attempt))
    raise LessonGenerationError(
        f"AI generation failed after {max_retries + 1} attempts: {last_error}"
    )


async def repair_lesson(
    provider: AIProvider,
    *,
    original_json: str,
    validation_error: Exception,
    system_prompt: str,
    schema: dict,
) -> str:
    repair_prompt = f"""
The lesson you generated failed validation.

Original output:
{original_json}

Validation errors:
{str(validation_error)}

Correct ONLY the violations. Return ONLY corrected JSON.
""".strip()
    return await retry_generate(
        provider, system_prompt=system_prompt, user_prompt=repair_prompt, schema=schema
    )


class LessonEngine:
    def __init__(self, provider: AIProvider, redis) -> None:
        self.provider = provider
        self.redis = redis

    async def generate(
        self,
        *,
        competency_map: CompetencyMap,
        system_prompt: str,
        user_prompt: str,
        prompt: PromptVersion,
        lesson_title: str,
    ) -> Lesson:
        schema = Lesson.model_json_schema()
        cache_key = calculate_cache_key(
            competency_map=competency_map, prompt=prompt, lesson_title=lesson_title
        )

        cached = await self.redis.get(cache_key)
        if cached:
            return Lesson.model_validate_json(cached)

        raw = await retry_generate(
            self.provider, system_prompt=system_prompt, user_prompt=user_prompt, schema=schema
        )

        try:
            lesson = Lesson.model_validate_json(raw)
        except ValidationError as first_error:
            repaired = await repair_lesson(
                self.provider,
                original_json=raw,
                validation_error=first_error,
                system_prompt=system_prompt,
                schema=schema,
            )
            try:
                lesson = Lesson.model_validate_json(repaired)
            except ValidationError as second_error:
                raise LessonGenerationError(
                    f"AI output remained invalid after repair: {second_error}"
                ) from second_error

        try:
            validate_competency_references(lesson, competency_map)
        except ValueError as biz_error:
            repaired = await repair_lesson(
                self.provider,
                original_json=lesson.model_dump_json(),
                validation_error=biz_error,
                system_prompt=system_prompt,
                schema=schema,
            )
            lesson = Lesson.model_validate_json(repaired)
            validate_competency_references(lesson, competency_map)

        await self.redis.set(cache_key, lesson.model_dump_json(), ex=7 * 24 * 60 * 60)
        return lesson
