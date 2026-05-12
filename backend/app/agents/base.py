from pathlib import Path
from typing import Generic, Type, TypeVar

from pydantic import BaseModel

from app.services.claude import ClaudeService

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"


class BaseAgent(Generic[InputT, OutputT]):
    name: str = "base"
    prompt_file: str = ""
    model: str = "claude-sonnet-4-20250514"

    def __init__(self, claude_service: ClaudeService):
        self.claude = claude_service
        self._system_prompt: str | None = None

    @property
    def system_prompt(self) -> str:
        if self._system_prompt is None:
            path = PROMPTS_DIR / self.prompt_file
            if path.exists():
                self._system_prompt = path.read_text()
            else:
                self._system_prompt = f"You are the {self.name} agent."
        return self._system_prompt

    def build_user_prompt(self, input_data: InputT) -> str:
        return input_data.model_dump_json(indent=2)

    async def run(self, input_data: InputT, output_schema: Type[OutputT]) -> OutputT:
        user_prompt = self.build_user_prompt(input_data)
        return await self.claude.generate(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            output_schema=output_schema,
            model=self.model,
        )
