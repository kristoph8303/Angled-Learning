from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from anthropic import Anthropic
from openai import OpenAI


class AIProvider(ABC):
    @abstractmethod
    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any],
    ) -> str:
        raise NotImplementedError


class OpenAIProvider(AIProvider):
    def __init__(
        self,
        client: OpenAI,
        model: str = "gpt-4o",
    ) -> None:
        self.client = client
        self.model = model

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any],
    ) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("OpenAI returned an empty response.")
        return content


class ClaudeProvider(AIProvider):
    def __init__(
        self,
        client: Anthropic,
        model: str = "claude-sonnet-4-5",
    ) -> None:
        self.client = client
        self.model = model

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any],
    ) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=8000,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            tools=[
                {
                    "name": "emit_lesson",
                    "description": "Return the validated lesson object.",
                    "input_schema": schema,
                }
            ],
            tool_choice={"type": "tool", "name": "emit_lesson"},
        )
        for block in response.content:
            if block.type == "tool_use":
                return json.dumps(block.input)
        raise RuntimeError("Claude did not return a structured tool result.")
