"""
GeminiThinking — Gemini subclass with native thinking and a unique registry id.

Studio uses model id as its unique key; giving both variants the same id causes
both to be selected simultaneously. This class appends '-thinking' to id so
Studio sees six distinct entries (three standard + three thinking).

The '-thinking' suffix exists only for Studio/registry display. Before every
API call the id is swapped to the real Gemini model id; it is restored
afterward so nothing outside the call ever sees the modified value.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Type, Union

from agno.models.google.gemini import Gemini
from agno.models.message import Message
from agno.models.response import ModelResponse
from agno.run.agent import RunOutput
from pydantic import BaseModel

THINKING_SUFFIX = "-thinking"
DEFAULT_THINKING_BUDGET = 5000


@dataclass
class GeminiThinking(Gemini):
    """
    Gemini with native chain-of-thought thinking.

    id  →  'gemini-2.5-flash-lite-thinking'   (Studio display / unique key)
    API →  'gemini-2.5-flash-lite'             (actual Gemini API model id)
    """

    # Populated in __post_init__ — the real API id without '-thinking' suffix
    _api_id: str = field(default="", init=False, repr=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        self._api_id = self.id.removesuffix(THINKING_SUFFIX)

    # ── context manager ──────────────────────────────────────────────────────

    @contextmanager
    def _real_id(self):
        """Temporarily replace self.id with the real Gemini API model id."""
        display = self.id
        self.id = self._api_id
        try:
            yield
        finally:
            self.id = display

    # ── invocation overrides ─────────────────────────────────────────────────

    def invoke(
        self,
        messages: List[Message],
        assistant_message: Message,
        response_format: Optional[Union[Dict, Type[BaseModel]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        run_response: Optional[RunOutput] = None,
        compress_tool_results: bool = False,
        retry_with_guidance: bool = False,
    ) -> ModelResponse:
        with self._real_id():
            return super().invoke(
                messages, assistant_message,
                response_format=response_format, tools=tools,
                tool_choice=tool_choice, run_response=run_response,
                compress_tool_results=compress_tool_results,
                retry_with_guidance=retry_with_guidance,
            )

    def invoke_stream(
        self,
        messages: List[Message],
        assistant_message: Message,
        response_format: Optional[Union[Dict, Type[BaseModel]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        run_response: Optional[RunOutput] = None,
        compress_tool_results: bool = False,
        retry_with_guidance: bool = False,
    ) -> Iterator[ModelResponse]:
        with self._real_id():
            yield from super().invoke_stream(
                messages, assistant_message,
                response_format=response_format, tools=tools,
                tool_choice=tool_choice, run_response=run_response,
                compress_tool_results=compress_tool_results,
                retry_with_guidance=retry_with_guidance,
            )

    async def ainvoke(
        self,
        messages: List[Message],
        assistant_message: Message,
        response_format: Optional[Union[Dict, Type[BaseModel]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        run_response: Optional[RunOutput] = None,
        compress_tool_results: bool = False,
        retry_with_guidance: bool = False,
    ) -> ModelResponse:
        with self._real_id():
            return await super().ainvoke(
                messages, assistant_message,
                response_format=response_format, tools=tools,
                tool_choice=tool_choice, run_response=run_response,
                compress_tool_results=compress_tool_results,
                retry_with_guidance=retry_with_guidance,
            )

    async def ainvoke_stream(
        self,
        messages: List[Message],
        assistant_message: Message,
        response_format: Optional[Union[Dict, Type[BaseModel]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        run_response: Optional[RunOutput] = None,
        compress_tool_results: bool = False,
        retry_with_guidance: bool = False,
    ) -> AsyncIterator[ModelResponse]:
        with self._real_id():
            async for chunk in super().ainvoke_stream(
                messages, assistant_message,
                response_format=response_format, tools=tools,
                tool_choice=tool_choice, run_response=run_response,
                compress_tool_results=compress_tool_results,
                retry_with_guidance=retry_with_guidance,
            ):
                yield chunk


def gemini_thinking(model_id: str, thinking_budget: int = DEFAULT_THINKING_BUDGET) -> GeminiThinking:
    """Convenience factory: returns a GeminiThinking for the given base model id."""
    return GeminiThinking(
        id=f"{model_id}{THINKING_SUFFIX}",
        provider="Google · Thinking",
        thinking_budget=thinking_budget,
        include_thoughts=True,
    )
