from typing import Type, TypeVar

import anthropic
from pydantic import BaseModel

from app.config import settings

T = TypeVar("T", bound=BaseModel)


class ClaudeService:
    def __init__(self, api_key: str | None = None):
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key or settings.anthropic_api_key
        )
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def _schema_to_tool(self, schema: Type[BaseModel]) -> dict:
        json_schema = schema.model_json_schema()
        json_schema.pop("title", None)
        return {
            "name": schema.__name__,
            "description": f"Output structured as {schema.__name__}",
            "input_schema": json_schema,
        }

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: Type[T],
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
    ) -> T:
        tool = self._schema_to_tool(output_schema)
        response = await self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            tools=[tool],
            tool_choice={"type": "tool", "name": tool["name"]},
            messages=[{"role": "user", "content": user_prompt}],
        )
        self.total_input_tokens += response.usage.input_tokens
        self.total_output_tokens += response.usage.output_tokens

        for block in response.content:
            if block.type == "tool_use":
                return output_schema.model_validate(block.input)

        raise ValueError("No tool_use block in response")

    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
    ) -> str:
        response = await self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        self.total_input_tokens += response.usage.input_tokens
        self.total_output_tokens += response.usage.output_tokens
        return response.content[0].text
