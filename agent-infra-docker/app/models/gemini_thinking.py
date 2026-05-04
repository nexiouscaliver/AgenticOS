"""
GeminiThinking — Gemini subclass with native thinking and a unique registry id.

Studio uses model id as its unique key; giving both variants the same id causes
both to be selected simultaneously. This class appends '-thinking' to id so
Studio sees six distinct entries (three standard + three thinking).

The '-thinking' suffix exists only for Studio/registry display. Before every
API call the id is swapped to the real Gemini model id; it is restored
afterward so nothing outside the call ever sees the modified value.

DB deserialization: Agno reconstructs models by calling
    get_model(f"{provider}:{id}")
which maps "Google" to a plain Gemini — losing our override. To fix this,
_install_agno_patch() below monkey-patches Agno's model registry so that any
id ending in '-thinking' is reconstructed as GeminiThinking rather than Gemini.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
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

    # ── context manager ──────────────────────────────────────────────────────

    @contextmanager
    def _real_id(self):
        """Temporarily replace self.id with the real Gemini API model id."""
        display = self.id
        self.id = display.removesuffix(THINKING_SUFFIX)
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
    """Convenience factory: returns a GeminiThinking for the given base model id.

    provider stays 'Google' so Agno can deserialize agents from the database.
    The '-thinking' suffix in id is enough to make Studio treat this as a
    distinct entry from the standard variant.
    """
    return GeminiThinking(
        id=f"{model_id}{THINKING_SUFFIX}",
        thinking_budget=thinking_budget,
        include_thoughts=True,
    )


def _install_agno_patch() -> None:
    """Patch Agno's model registry so ids ending in '-thinking' round-trip correctly.

    When Agno loads an agent from the database it calls:
        get_model("Google:gemini-2.5-flash-lite-thinking")
    which normally returns a plain Gemini — losing our id-swap override.
    This patch intercepts that lookup and returns a GeminiThinking instance
    so the '-thinking' suffix is stripped before every API call.
    """
    import agno.models.utils as _utils

    if getattr(_utils, "_gemini_thinking_patched", False):
        return

    _original = _utils._get_model_class

    def _patched(model_id: str, model_provider: str):
        if model_provider == "google" and model_id.endswith(THINKING_SUFFIX):
            return GeminiThinking(
                id=model_id,
                thinking_budget=DEFAULT_THINKING_BUDGET,
                include_thoughts=True,
            )
        return _original(model_id, model_provider)

    _utils._get_model_class = _patched
    _utils._gemini_thinking_patched = True  # type: ignore[attr-defined]


# Auto-patch when this module is imported so DB deserialization always works.
_install_agno_patch()
