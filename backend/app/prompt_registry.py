from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptRecord:
    name: str
    version: int
    template: str
    output_schema_name: str
    output_schema_version: str
    model_provider: str
    model_name: str
    active: bool = False


class PromptRegistry:
    def __init__(self) -> None:
        self._prompts: dict[tuple[str, int], PromptRecord] = {}

    def register(self, prompt: PromptRecord) -> None:
        key = (prompt.name, prompt.version)
        if key in self._prompts:
            raise ValueError(f"Prompt version already exists: {key}")
        self._prompts[key] = prompt

    def get(self, name: str, version: int) -> PromptRecord:
        try:
            return self._prompts[(name, version)]
        except KeyError as exc:
            raise KeyError(f"Prompt not found: {name} v{version}") from exc

    def activate(self, name: str, version: int) -> PromptRecord:
        target = self.get(name, version)
        for key, prompt in self._prompts.items():
            if prompt.name == name:
                self._prompts[key] = PromptRecord(
                    **{**prompt.__dict__, "active": (prompt.version == version)}
                )
        return target
