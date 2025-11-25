"""
GLM4.5 Provider implementation compatible with Agno's OpenAI-like interface.
"""

import os
import time
import logging
from typing import Any, Dict, Iterator, List, Optional, Union, Type
from dataclasses import dataclass, field
from enum import Enum

from agno.models.openai.like import OpenAILike
from agno.models.message import Message
from agno.models.response import ModelResponse
from pydantic import BaseModel


logging.basicConfig(level=logging.INFO)
glm_logger = logging.getLogger(__name__)


class GLM45Mode(Enum):
    THINKING = "thinking"
    NON_THINKING = "non_thinking"
    HYBRID = "hybrid"


@dataclass
class GLM45Config:
    enable_thinking: bool = True
    thinking_budget: int = 32768
    enable_reflection: bool = True
    reasoning_effort: str = "high"
    tool_choice: str = "auto"
    enable_search: bool = True
    arabic_optimization: bool = True
    response_format: Optional[Dict] = None
    safety_settings: Dict = field(default_factory=lambda: {
        "harassment": "BLOCK_MEDIUM_AND_ABOVE",
        "hate_speech": "BLOCK_MEDIUM_AND_ABOVE",
        "dangerous_content": "BLOCK_MEDIUM_AND_ABOVE"
    })


class QueryComplexityAnalyzer:
    def __init__(self):
        self.complex_indicators = [
            'analyze', 'compare', 'evaluate', 'explain why', 'how does',
            'what if', 'design', 'optimize', 'debug', 'solve',
            'تحليل', 'مقارنة', 'تقييم', 'شرح', 'كيف'
        ]
        self.simple_indicators = [
            'what is', 'define', 'list', 'name', 'when', 'where',
            'ما هو', 'عرف', 'اذكر', 'متى', 'أين'
        ]

    def analyze(self, query: str) -> str:
        query_lower = query.lower()
        complex_score = sum(1 for indicator in self.complex_indicators if indicator in query_lower)
        simple_score = sum(1 for indicator in self.simple_indicators if indicator in query_lower)
        word_count = len(query.split())
        has_multiple_questions = query.count('?') > 1 or query.count('؟') > 1
        if complex_score >= 2 or (complex_score >= 1 and word_count > 50):
            return 'very_complex'
        elif complex_score >= 1 or has_multiple_questions:
            return 'complex'
        elif simple_score >= 1 and word_count < 20:
            return 'simple'
        else:
            return 'moderate'


class GLM45Provider(OpenAILike):
    def __init__(
        self,
        id: str = "glm-4.5",
        base_url: str = "https://api.z.ai/api/paas/v4",
        api_key: str = os.getenv("GLM_API_KEY"),
        mode: GLM45Mode = GLM45Mode.HYBRID,
        thinking_type: Optional[str] = None,
        config: Optional[GLM45Config] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        top_p: float = 0.9,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        stop: Optional[List[str]] = None,
        stream: bool = True,
        **kwargs
    ):
        super().__init__(
            id=id,
            base_url=base_url,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            stop=stop or ["<|endoftext|>", "<|endofthinking|>"],
            **kwargs
        )

        self.mode = mode
        self.config = config or GLM45Config()

        self.client_thinking_type: Optional[str] = None
        if isinstance(thinking_type, str):
            tt = thinking_type.strip().lower()
            if tt in ("enabled", "disabled", "auto"):
                self.client_thinking_type = tt
        self._query_analyzer = QueryComplexityAnalyzer()

        self.thinking_tokens_used = 0
        self.total_thinking_time = 0.0
        self._use_thinking_for_next_request: Optional[bool] = None

        glm_logger.info(f"Initialized GLM4.5 Provider in {mode.value} mode")

    def _should_use_thinking(self, messages: List[Message]) -> bool:
        if self.client_thinking_type == "enabled":
            return True
        if self.client_thinking_type == "disabled":
            return False
        if self.mode == GLM45Mode.THINKING:
            return True
        elif self.mode == GLM45Mode.NON_THINKING:
            return False
        else:
            last_message = messages[-1] if messages else None
            if last_message:
                complexity = self._query_analyzer.analyze(last_message.content)
                return complexity in ['complex', 'very_complex']
            return False

    def _prepare_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        formatted_messages = []
        for msg in messages:
            content = msg.content
            formatted_msg = {
                "role": msg.role,
                "content": content
            }
            if hasattr(msg, 'function_call') and msg.function_call:
                formatted_msg["function_call"] = msg.function_call
            formatted_messages.append(formatted_msg)
        return formatted_messages

    def _preprocess_arabic(self, text: str) -> str:
        import re
        text = re.sub(r'[\u064B-\u0652\u0670\u0640]', '', text)
        text = re.sub(r'[إأٱآا]', 'ا', text)
        text = re.sub(r'[ىئ]', 'ي', text)
        text = re.sub(r'ـ', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _contains_arabic(self, text: str) -> bool:
        import re
        arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+')
        return bool(arabic_pattern.search(text))

    def get_request_params(
        self,
        response_format: Optional[Union[Dict, Type[BaseModel]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        params = super().get_request_params(
            response_format=response_format, tools=tools, tool_choice=tool_choice
        )
        if self._use_thinking_for_next_request is None:
            use_thinking = True if self.mode == GLM45Mode.THINKING else False
        else:
            use_thinking = self._use_thinking_for_next_request
        extra_body = params.setdefault("extra_body", {})
        extra_body["thinking"] = {"type": "enabled" if use_thinking else "disabled"}
        if not use_thinking:
            extra_body["chat_template_kwargs"] = {"enable_thinking": False}
        else:
            extra_body["thinking_config"] = {
                "enabled": True,
                "budget": self.config.thinking_budget,
                "reflection": self.config.enable_reflection,
                "effort": self.config.reasoning_effort,
            }
        if tool_choice is None:
            requested_tool_choice = self.config.tool_choice or "auto"
            if requested_tool_choice not in ("auto", "none", "required"):
                requested_tool_choice = "auto"
            
            # Only set tool_choice if tools are present
            if tools:
                extra_body["tool_choice"] = requested_tool_choice
        else:
            # If tool_choice is explicitly passed, we should respect it
            # But we should still probably check if tools are present if it's not "none"
            if tool_choice != "none" and not tools:
                # If tool_choice is requested but no tools, don't send tool_choice
                pass
            else:
                extra_body["tool_choice"] = tool_choice

        if self.config.response_format:
            extra_body["response_format"] = self.config.response_format
        extra_body["safety_settings"] = self.config.safety_settings
        body = params.setdefault("extra_body", {})
        if "max_output_tokens" not in body:
            body["max_output_tokens"] = getattr(self, "max_tokens", 8192)
        if "max_input_tokens" not in body:
            body["max_input_tokens"] = 131072
        return params

    def parse_provider_response(self, response: Any, **kwargs) -> ModelResponse:
        try:
            base_parsed = super().parse_provider_response(response, **kwargs)
            if not isinstance(base_parsed, ModelResponse):
                return base_parsed
            content = base_parsed.content if isinstance(base_parsed.content, str) else ""
            use_thinking_now = (
                self._use_thinking_for_next_request
                if self._use_thinking_for_next_request is not None
                else (self.mode == GLM45Mode.THINKING)
            )
            thinking_from_provider = None
            try:
                choices = None
                if isinstance(response, dict):
                    choices = response.get("choices")
                elif hasattr(response, "choices"):
                    choices = getattr(response, "choices")
                if choices and len(choices) > 0:
                    choice0 = choices[0]
                    message = choice0.get("message") if isinstance(choice0, dict) else getattr(choice0, "message", None)
                    thinking_from_provider = self._extract_thinking_from_message(message)
            except Exception:
                pass
            new_content = content
            if use_thinking_now:
                wrapped = self._extract_and_wrap_thinking_from_text(content)
                if wrapped is not None:
                    new_content = wrapped
                elif thinking_from_provider:
                    new_content = f"<thinking>\n{thinking_from_provider}\n</thinking>\n\n{content}"
            else:
                stripped = self._strip_thinking_from_text(content)
                if stripped is not None:
                    new_content = stripped
            base_parsed.content = new_content
            return base_parsed
        except Exception as e:
            glm_logger.error(f"Error parsing GLM 4.5 provider response: {e}")
            return ModelResponse(content="")

    def _extract_thinking_from_message(self, message: Any) -> Optional[str]:
        if message is None:
            return None
        field_names = [
            "reasoning_content", "thinking_content", "thinking", "thought",
            "reasoning", "internal_thought", "rationale", "analysis"
        ]
        try:
            for name in field_names:
                if isinstance(message, dict):
                    if name in message and isinstance(message[name], str) and message[name].strip():
                        return message[name].strip()
                else:
                    if hasattr(message, name):
                        value = getattr(message, name)
                        if isinstance(value, str) and value.strip():
                            return value.strip()
        except Exception:
            pass
        content = None
        if isinstance(message, dict):
            content = message.get("content")
        else:
            content = getattr(message, "content", None)
        if isinstance(content, str) and '<thinking>' in content and '</thinking>' in content:
            try:
                import re
                match = re.search(r'<thinking>([\s\S]*?)</thinking>', content)
                if match:
                    return match.group(1).strip()
            except Exception:
                return None
        return None

    def invoke(self, messages: List[Message], **kwargs) -> ModelResponse:
        start_time = time.time()
        if self.config.arabic_optimization:
            for msg in messages:
                if isinstance(msg.content, str) and self._contains_arabic(msg.content):
                    msg.content = self._preprocess_arabic(msg.content)
        use_thinking = self._should_use_thinking(messages)
        glm_logger.debug(f"Using {'thinking' if use_thinking else 'non-thinking'} mode")
        self._use_thinking_for_next_request = use_thinking
        try:
            response = super().invoke(messages, **kwargs)
            try:
                if response and hasattr(response, "content") and isinstance(response.content, str):
                    use_thinking_now = (
                        self._use_thinking_for_next_request
                        if self._use_thinking_for_next_request is not None
                        else (self.mode == GLM45Mode.THINKING)
                    )
                    if use_thinking_now:
                        new_content = self._extract_and_wrap_thinking_from_text(response.content)
                        if new_content is not None:
                            response.content = new_content
                    else:
                        stripped = self._strip_thinking_from_text(response.content)
                        if stripped is not None:
                            response.content = stripped
            except Exception:
                pass
            if use_thinking and hasattr(response, "usage"):
                try:
                    usage = response.usage
                    thinking_tokens = 0
                    if isinstance(usage, dict):
                        thinking_tokens = (
                            usage.get("completion_tokens_details", {}).get("reasoning_tokens", 0)
                            or usage.get("thinking_tokens", 0)
                        )
                    else:
                        ctd = getattr(usage, "completion_tokens_details", None)
                        if isinstance(ctd, dict):
                            thinking_tokens = ctd.get("reasoning_tokens", 0) or 0
                        elif ctd is not None:
                            thinking_tokens = getattr(ctd, "reasoning_tokens", 0) or 0
                        else:
                            thinking_tokens = getattr(usage, "reasoning_tokens", 0) or 0
                    if isinstance(thinking_tokens, (int, float)):
                        self.thinking_tokens_used += int(thinking_tokens)
                        self.total_thinking_time += (time.time() - start_time)
                except Exception:
                    pass
            return response
        except Exception as e:
            glm_logger.error(f"Error invoking GLM4.5: {str(e)}")
            raise
        finally:
            self._use_thinking_for_next_request = None

    def invoke_stream(
        self,
        messages: List[Message],
        **kwargs
    ) -> Iterator[Union[str, ModelResponse]]:
        if self.config.arabic_optimization:
            for msg in messages:
                if isinstance(msg.content, str) and self._contains_arabic(msg.content):
                    msg.content = self._preprocess_arabic(msg.content)
        use_thinking = self._should_use_thinking(messages)
        self._use_thinking_for_next_request = use_thinking
        in_thinking_block = False
        in_tag_thinking_block = False
        thinking_content: List[str] = []
        try:
            for raw_chunk in super().invoke_stream(messages, **kwargs):
                chunk_text: Optional[str] = None
                is_model_response = hasattr(raw_chunk, "content")
                original_chunk = raw_chunk
                if isinstance(raw_chunk, str):
                    chunk_text = raw_chunk
                elif is_model_response and isinstance(getattr(raw_chunk, "content", None), str):
                    chunk_text = raw_chunk.content
                if not use_thinking:
                    if chunk_text is None:
                        yield original_chunk
                        continue
                    text = chunk_text
                    if '<|thinking|>' in text:
                        in_thinking_block = True
                        text = text.split('<|thinking|>', 1)[0]
                    if in_thinking_block:
                        if '<|endofthinking|>' in text:
                            after_end = text.split('<|endofthinking|>', 1)[1]
                            in_thinking_block = False
                            text = after_end
                        else:
                            continue
                    while True:
                        if in_tag_thinking_block:
                            if '</thinking>' in text:
                                text = text.split('</thinking>', 1)[1]
                                in_tag_thinking_block = False
                                continue
                            else:
                                text = ''
                                break
                        else:
                            if '<thinking>' in text and '</thinking>' in text:
                                pre, rest = text.split('<thinking>', 1)
                                _, post = rest.split('</thinking>', 1)
                                text = pre + post
                                continue
                            elif '<thinking>' in text:
                                text = text.split('<thinking>', 1)[0]
                                in_tag_thinking_block = True
                                break
                            else:
                                break
                    if text:
                        if is_model_response:
                            original_chunk.content = text
                            yield original_chunk
                        else:
                            yield ModelResponse(content=text)
                    continue
                text = chunk_text
                if '<|thinking|>' in text:
                    in_thinking_block = True
                    text = text.split('<|thinking|>', 1)[1]
                if in_thinking_block:
                    if '<|endofthinking|>' in text:
                        before_end, after_end = text.split('<|endofthinking|>', 1)
                        thinking_content.append(before_end)
                        wrapped = f"<thinking>\n{''.join(thinking_content)}\n</thinking>\n\n"
                        thinking_content.clear()
                        in_thinking_block = False
                        yield ModelResponse(content=wrapped)
                        if after_end:
                            if is_model_response:
                                original_chunk.content = after_end
                                yield original_chunk
                            else:
                                yield ModelResponse(content=after_end)
                        continue
                    else:
                        thinking_content.append(text)
                        continue
                if is_model_response:
                    original_chunk.content = text
                    yield original_chunk
                else:
                    yield ModelResponse(content=text)
        except Exception as e:
            glm_logger.error(f"Error in GLM4.5 stream: {str(e)}")
            raise
        finally:
            self._use_thinking_for_next_request = None

    def _extract_and_wrap_thinking_from_text(self, text: str) -> Optional[str]:
        try:
            import re
            pattern = re.compile(r"<\|thinking\|>([\s\S]*?)<\|endofthinking\|>")
            match = pattern.search(text)
            if not match:
                return None
            thinking = match.group(1).strip()
            main = pattern.sub("", text).strip()
            return f"<thinking>\n{thinking}\n</thinking>\n\n{main}"
        except Exception:
            return None

    def _strip_thinking_from_text(self, text: str) -> Optional[str]:
        try:
            import re
            original = text
            text = re.sub(r"<\|thinking\|>[\s\S]*?<\|endofthinking\|>", "", text)
            text = re.sub(r"<thinking>[\s\S]*?</thinking>", "", text)
            new_text = text.strip()
            return new_text if new_text != original else None
        except Exception:
            return None

    def set_mode(self, mode: GLM45Mode):
        self.mode = mode
        glm_logger.info(f"Changed GLM4.5 mode to {mode.value}")

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "mode": self.mode.value,
            "thinking_tokens_used": self.thinking_tokens_used,
            "total_thinking_time": self.total_thinking_time,
            "average_thinking_time": (
                self.total_thinking_time / max(1, self.thinking_tokens_used)
                if self.thinking_tokens_used > 0 else 0
            ),
            "arabic_optimization": self.config.arabic_optimization,
            "reasoning_effort": self.config.reasoning_effort
        }

    def reset_metrics(self):
        self.thinking_tokens_used = 0
        self.total_thinking_time = 0.0


