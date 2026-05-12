import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pydantic import BaseModel

from app.services.claude import ClaudeService


class MockOutput(BaseModel):
    answer: str
    score: int


@pytest.mark.asyncio
async def test_generate_returns_structured_output():
    service = ClaudeService(api_key="test-key")

    mock_response = MagicMock()
    mock_content_block = MagicMock()
    mock_content_block.type = "tool_use"
    mock_content_block.input = {"answer": "yes", "score": 85}
    mock_response.content = [mock_content_block]
    mock_response.usage = MagicMock(input_tokens=100, output_tokens=50)

    with patch.object(
        service.client.messages, "create", new_callable=AsyncMock, return_value=mock_response
    ):
        result = await service.generate(
            system_prompt="You are a test agent.",
            user_prompt="Test question",
            output_schema=MockOutput,
        )
        assert result.answer == "yes"
        assert result.score == 85


def test_schema_to_tool_converts_pydantic_model():
    service = ClaudeService(api_key="test-key")
    tool = service._schema_to_tool(MockOutput)
    assert tool["name"] == "MockOutput"
    assert "answer" in tool["input_schema"]["properties"]
    assert "score" in tool["input_schema"]["properties"]
