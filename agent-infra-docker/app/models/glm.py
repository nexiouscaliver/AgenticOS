import json
import os
import time
import logging
from typing import Any, Dict, Iterator, List, Optional, Union, Type
from dataclasses import dataclass, field
from enum import Enum

from agno.models.openai.like import OpenAILike
from agno.models.message import Message
from agno.models.response import ModelResponse
from agno.run.agent import RunOutput
from agno.run.team import TeamRunOutput
from pydantic import BaseModel

# Import OpenAI types needed at runtime
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk

# try:
#     from zai import ZaiClient
# except ImportError:
#     logger.error("ZaiClient not available. Please install zai-sdk: pip install zai-sdk")
#     raise ImportError("ZaiClient not available. Please install zai-sdk: pip install zai-sdk")


# Configure logging with environment variable control
_log_level_str = os.getenv("GLM_LOG_LEVEL", "INFO").upper()
_log_level = getattr(logging, _log_level_str, logging.INFO)
logging.basicConfig(level=_log_level)
glm_logger = logging.getLogger(__name__)
glm_logger.setLevel(_log_level)
glm_logger.info(f"GLM Logger initialized with level: {_log_level_str}")

# Import tiktoken for token counting (after logger is initialized)
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    glm_logger.warning("tiktoken not available, will use character-based estimation for token counting")


class GLM45Mode(Enum):
    """GLM4.5 operation modes"""
    THINKING = "thinking"  # Full reasoning with internal thoughts
    NON_THINKING = "non_thinking"  # Direct response without reasoning
    HYBRID = "hybrid"  # Automatic mode selection based on query complexity


@dataclass
class GLM45Config:
    """Configuration for GLM4.5 specific parameters"""
    enable_thinking: bool = True
    thinking_budget: int = 32768  # Max tokens for thinking process
    enable_reflection: bool = True  # Enable self-reflection in thinking
    reasoning_effort: str = "high"  # low, medium, high
    tool_choice: str = "auto"  # auto, none, required
    enable_search: bool = True  # Enable knowledge base search
    arabic_optimization: bool = True  # Enable Arabic-specific optimizations
    response_format: Optional[Dict] = None  # Structured output format
    safety_settings: Dict = field(default_factory=lambda: {
        "harassment": "BLOCK_MEDIUM_AND_ABOVE",
        "hate_speech": "BLOCK_MEDIUM_AND_ABOVE",
        "dangerous_content": "BLOCK_MEDIUM_AND_ABOVE"
    })

class QueryComplexityAnalyzer:
    """
    Analyzer to determine query complexity for hybrid mode decisions
    """

    def __init__(self):
        self.complex_indicators = [
            'analyze', 'compare', 'evaluate', 'explain why', 'how does',
            'what if', 'design', 'optimize', 'debug', 'solve',
            'تحليل', 'مقارنة', 'تقييم', 'شرح', 'كيف'  # Arabic indicators
        ]

        self.simple_indicators = [
            'what is', 'define', 'list', 'name', 'when', 'where',
            'ما هو', 'عرف', 'اذكر', 'متى', 'أين'  # Arabic indicators
        ]

    def analyze(self, query: str) -> str:
        """
        Analyze query complexity
        
        Args:
            query: Input query text
            
        Returns:
            Complexity level: 'simple', 'moderate', 'complex', 'very_complex'
        """
        query_lower = query.lower()

        # Check for complex indicators
        complex_score = sum(1 for indicator in self.complex_indicators
                          if indicator in query_lower)

        # Check for simple indicators
        simple_score = sum(1 for indicator in self.simple_indicators
                         if indicator in query_lower)

        # Analyze based on length and structure
        word_count = len(query.split())
        has_multiple_questions = query.count('?') > 1 or query.count('؟') > 1

        # Determine complexity
        if complex_score >= 2 or (complex_score >= 1 and word_count > 50):
            return 'very_complex'
        elif complex_score >= 1 or has_multiple_questions:
            return 'complex'
        elif simple_score >= 1 and word_count < 20:
            return 'simple'
        else:
            return 'moderate'


class GLM45Provider(OpenAILike):
    """
    Custom GLM4.5 Provider for Agno Framework
    
    This provider extends OpenAILike to support GLM4.5's advanced features:
    - Thinking and non-thinking modes
    - Hybrid reasoning with automatic mode selection
    - Arabic text optimization
    - Tool calling with reflection
    - Streaming support with thinking tokens
    
    Example usage:
    ```python
    from agno.agent import Agent
    
    provider = GLM45Provider(
        base_url="http://localhost:8000/v1",
        api_key="your-api-key",
        mode=GLM45Mode.HYBRID,
        config=GLM45Config(
            enable_thinking=True,
            arabic_optimization=True,
            reasoning_effort="high"
        )
    )
    
    agent = Agent(
        model=provider,
        knowledge=your_knowledge_base,
        search_knowledge=True
    )
    ```
    """

    def __init__(
        self,
        id: str = "glm-4.5",
        base_url = "https://api.z.ai/api/paas/v4",
        api_key: str = os.getenv("GLM_API_KEY"),
        mode: GLM45Mode = GLM45Mode.HYBRID,
        thinking_type: Optional[str] = None,
        config: Optional[GLM45Config] = None,
        temperature: float = 0.7,
        max_tokens: int = 90000,
        top_p: float = 0.9,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        stop: Optional[List[str]] = None,
        stream: bool = True,
        # Retry configuration
        max_retries: int = int(os.getenv("GLM_MAX_RETRIES", 5)),
        initial_retry_delay: float = float(os.getenv("GLM_INITIAL_RETRY_DELAY", 1.0)),
        **kwargs
    ):
        """
        Initialize GLM4.5 Provider
        
        Args:
            id: Model identifier (glm-4.5-air or glm-4.5)
            base_url: vLLM or API endpoint URL
            api_key: API key for authentication
            mode: Operation mode (THINKING, NON_THINKING, HYBRID)
            config: GLM4.5 specific configuration
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            frequency_penalty: Frequency penalty (-2.0 to 2.0)
            presence_penalty: Presence penalty (-2.0 to 2.0)
            stop: Stop sequences
            stream: Enable streaming responses
            **kwargs: Additional OpenAILike parameters
        """
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
            # stream=stream,
            **kwargs
        )

        self.mode = mode
        self.config = config or GLM45Config()
        # Global kill-switch flag used to permanently disable thinking mode
        self.force_disable_thinking: bool = False
        # Store retry configuration
        self.max_retries = max(0, int(max_retries))
        # Ensure a sane minimum positive delay
        try:
            delay = float(initial_retry_delay)
            self.initial_retry_delay = delay if delay > 0 else 1.0
        except Exception:
            self.initial_retry_delay = 1.0
        # Normalize client-provided thinking type (enabled|disabled|auto)
        self.client_thinking_type: Optional[str] = None
        if isinstance(thinking_type, str):
            tt = thinking_type.strip().lower()
            if tt in ("enabled", "disabled", "auto"):
                self.client_thinking_type = tt
        # If a caller already toggled the kill-switch before init completes,
        # respect it by forcing mode + thinking_type immediately.
        if self.force_disable_thinking:
            self.mode = GLM45Mode.NON_THINKING
            self.client_thinking_type = "disabled"
            self.config.enable_thinking = False
        self._query_analyzer = QueryComplexityAnalyzer()

        # Track thinking tokens for billing/monitoring
        self.thinking_tokens_used = 0
        self.total_thinking_time = 0.0
        # Thinking mode to apply for the next request (set in invoke/invoke_stream)
        self._use_thinking_for_next_request: Optional[bool] = None

        # Dynamic max_tokens configuration
        # API context limit: actual maximum context window supported by the API (92,160 for GLM-4.5)
        self.api_context_limit = int(os.getenv("GLM_API_CONTEXT_LIMIT", "92160"))
        # Safe output limit: conservative limit to prevent overflow (default: 90,000)
        self.safe_output_limit = int(os.getenv("GLM_SAFE_OUTPUT_LIMIT", "90000"))
        # Safety buffer: margin to prevent edge cases
        self.context_safety_buffer = int(os.getenv("GLM_CONTEXT_SAFETY_BUFFER", "2000"))
        # Estimation safety margin: accounts for token counting discrepancies (default: 3000)
        # This covers overhead from system prompts, tool definitions, formatting, etc.
        self.estimation_safety_margin = int(os.getenv("GLM_ESTIMATION_SAFETY_MARGIN", "3000"))
        
        # Initialize tiktoken encoder once for efficiency
        self._tiktoken_encoder = None
        if TIKTOKEN_AVAILABLE:
            try:
                self._tiktoken_encoder = tiktoken.get_encoding("cl100k_base")
                glm_logger.debug("Initialized tiktoken encoder (cl100k_base) for token counting")
            except Exception as e:
                glm_logger.warning(f"Failed to initialize tiktoken encoder: {e}")
                self._tiktoken_encoder = None

        glm_logger.info(
            f"Initialized GLM4.5 Provider in {mode.value} mode "
            f"(api_context_limit={self.api_context_limit}, safe_output_limit={self.safe_output_limit}, "
            f"buffer={self.context_safety_buffer}, estimation_margin={self.estimation_safety_margin})"
        )

    def _estimate_message_tokens(self, messages: List[Message]) -> int:
        """
        Estimate token count for a list of messages using tiktoken.
        
        Falls back to character-based estimation if tiktoken is unavailable.
        Includes overhead for role markers and message formatting.
        
        Args:
            messages: List of Message objects or dicts
            
        Returns:
            Estimated token count for the entire message list
        """
        total_tokens = 0
        
        try:
            if self._tiktoken_encoder is not None:
                # Use tiktoken for accurate counting
                for msg in messages:
                    # Handle both Message objects and dicts
                    if isinstance(msg, Message):
                        role = msg.role or "user"
                        content = msg.content or ""
                    elif isinstance(msg, dict):
                        role = msg.get("role", "user")
                        content = msg.get("content", "")
                    else:
                        # Unknown format, convert to string
                        content = str(msg)
                        role = "user"
                    
                    # Count tokens in content
                    if isinstance(content, str):
                        total_tokens += len(self._tiktoken_encoder.encode(content))
                    elif isinstance(content, list):
                        # Handle multi-part content (text + images)
                        for part in content:
                            if isinstance(part, dict):
                                if part.get("type") == "text":
                                    text = part.get("text", "")
                                    total_tokens += len(self._tiktoken_encoder.encode(text))
                                elif part.get("type") == "image_url":
                                    # Rough estimate for images: 85 tokens per 512x512 tile
                                    total_tokens += 85
                    
                    # Add overhead for role and formatting (~4 tokens per message)
                    total_tokens += 4
                
                # Add 3 tokens for message priming
                total_tokens += 3
                
                glm_logger.debug(f"Estimated {total_tokens} tokens using tiktoken for {len(messages)} messages")
                return total_tokens
            
            else:
                # Fallback: character-based estimation
                for msg in messages:
                    if isinstance(msg, Message):
                        content = msg.content or ""
                    elif isinstance(msg, dict):
                        content = msg.get("content", "")
                    else:
                        content = str(msg)
                    
                    if isinstance(content, str):
                        # Rough estimate: 4 characters per token
                        total_tokens += max(1, len(content) // 4)
                    elif isinstance(content, list):
                        for part in content:
                            if isinstance(part, dict) and part.get("type") == "text":
                                text = part.get("text", "")
                                total_tokens += max(1, len(text) // 4)
                    
                    # Add overhead
                    total_tokens += 4
                
                total_tokens += 3
                glm_logger.debug(f"Estimated {total_tokens} tokens using character count for {len(messages)} messages (tiktoken unavailable)")
                return total_tokens
                
        except Exception as e:
            # Last resort: very rough estimation
            glm_logger.warning(f"Error during token estimation: {e}. Using very rough estimation.")
            total_chars = 0
            for msg in messages:
                try:
                    if isinstance(msg, Message):
                        content = str(msg.content or "")
                    elif isinstance(msg, dict):
                        content = str(msg.get("content", ""))
                    else:
                        content = str(msg)
                    total_chars += len(content)
                except Exception:
                    pass
            
            estimated = max(100, total_chars // 4)
            glm_logger.debug(f"Emergency token estimation: {estimated} tokens")
            return estimated

    def enforce_non_thinking(self, reason: str = "system") -> None:
        """
        Permanently disable thinking mode for this provider instance.

        Args:
            reason: Optional context for logging/diagnostics
        """
        self.force_disable_thinking = True
        self.mode = GLM45Mode.NON_THINKING
        self.client_thinking_type = "disabled"
        self.config.enable_thinking = False
        glm_logger.info(
            "[GLM Provider] 🚫 Thinking disabled (reason=%s, model=%s)",
            reason,
            self.id,
        )

    def _should_use_thinking(self, messages: List[Message]) -> bool:
        """
        Determine whether to use thinking mode based on OPT-IN principle.
        
        CORE PRINCIPLE: Thinking mode is OPT-IN ONLY - Never use thinking mode 
        unless the user explicitly requests it via thinking_mode=true or thinking_type="enabled".
        
        Args:
            messages: Conversation messages
            
        Returns:
            bool: True if thinking mode should be used (only when user explicitly enabled it)
        """
        # ═══════════════════════════════════════════════════════════════
        # OPT-IN ENFORCEMENT: Check user request FIRST before any mode/complexity checks
        # ═══════════════════════════════════════════════════════════════
        
        # 0. Hard kill-switch → Always disabled
        if getattr(self, "force_disable_thinking", False):
            glm_logger.debug("[Thinking Decision] force_disable_thinking flag active → DISABLED")
            return False

        # 1. User explicitly disabled thinking → Return False
        if self.client_thinking_type == "disabled":
            glm_logger.debug("[Thinking Decision] User explicitly disabled thinking → DISABLED")
            return False
        
        # 2. User explicitly enabled thinking → Return True (OPT-IN satisfied)
        if self.client_thinking_type == "enabled":
            glm_logger.debug("[Thinking Decision] User explicitly enabled thinking → ENABLED")
            return True
        
        # 3. User set "auto" or None → Return False (OPT-IN: no explicit request = disabled)
        # "auto" does NOT mean auto-enable based on complexity - it means disabled unless user enables
        if self.client_thinking_type == "auto" or self.client_thinking_type is None:
            glm_logger.debug(
                f"[Thinking Decision] No explicit user request (thinking_type={self.client_thinking_type}) → DISABLED (opt-in principle)"
            )
            return False
        
        # ═══════════════════════════════════════════════════════════════
        # Mode checks (only reached if client_thinking_type is not set)
        # ═══════════════════════════════════════════════════════════════
        
        # NON_THINKING mode → Always disabled
        if self.mode == GLM45Mode.NON_THINKING:
            glm_logger.debug("[Thinking Decision] Mode is NON_THINKING → DISABLED")
            return False
        
        # THINKING mode → Only enabled if user requested it (already checked above)
        # If we reach here with THINKING mode but no user request, disable it (opt-in)
        if self.mode == GLM45Mode.THINKING:
            glm_logger.warning(
                "[Thinking Decision] Mode is THINKING but no user request found → DISABLED (opt-in principle)"
            )
            return False
        
        # HYBRID mode → Disabled by default (opt-in principle)
        # HYBRID should NOT auto-enable thinking based on query complexity
        # Only enable if user explicitly requested it (already checked above)
        if self.mode == GLM45Mode.HYBRID:
            glm_logger.debug(
                "[Thinking Decision] Mode is HYBRID but no user request → DISABLED (opt-in principle, no auto-enable)"
            )
            return False
        
        # Fallback: Default to disabled (opt-in principle)
        glm_logger.debug("[Thinking Decision] Fallback → DISABLED (opt-in principle)")
        return False

    def _prepare_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """
        Prepare messages for GLM4.5 API with Arabic preprocessing
        
        Args:
            messages: List of conversation messages
            
        Returns:
            List of formatted message dictionaries
        """
        formatted_messages = []

        for msg in messages:
            content = msg.content

            # Apply Arabic preprocessing if enabled
            # if self.config.arabic_optimization and self._contains_arabic(content):
            #     content = self._preprocess_arabic(content)

            formatted_msg = {
                "role": msg.role,
                "content": content
            }

            # Add function call information if present
            if hasattr(msg, 'function_call') and msg.function_call:
                formatted_msg["function_call"] = msg.function_call

            formatted_messages.append(formatted_msg)

        return formatted_messages

    def _preprocess_arabic(self, text: str) -> str:
        """
        Preprocess Arabic text for optimal GLM4.5 processing
        
        Args:
            text: Input text containing Arabic
            
        Returns:
            Preprocessed text
        """
        import re

        # Remove Arabic diacritics (tashkeel)
        text = re.sub(r'[\u064B-\u0652\u0670\u0640]', '', text)

        # Normalize Alef variants
        text = re.sub(r'[إأٱآا]', 'ا', text)

        # Normalize Yeh variants
        text = re.sub(r'[ىئ]', 'ي', text)

        # Remove kashida (tatweel)
        text = re.sub(r'ـ', '', text)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _contains_arabic(self, text: str) -> bool:
        """Check if text contains Arabic characters"""
        import re
        arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+')
        return bool(arabic_pattern.search(text))

    def get_request_params(
        self,
        response_format: Optional[Union[Dict, Type[BaseModel]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        run_response: Optional[Union[RunOutput, TeamRunOutput]] = None,
    ) -> Dict[str, Any]:
        """
        Get request parameters with GLM4.5 specific configurations.
        This overrides the parent's method but keeps a compatible signature.
        """
        params = super().get_request_params(
            response_format=response_format, 
            tools=tools, 
            tool_choice=tool_choice
        )

        # Decide thinking mode based on the flag set for this request
        # If not explicitly set, fallback to a safe default based on configured mode
        if self._use_thinking_for_next_request is None:
            use_thinking = True if self.mode == GLM45Mode.THINKING else False
        else:
            use_thinking = self._use_thinking_for_next_request

        # Add GLM4.5 specific parameters
        extra_body = params.setdefault("extra_body", {})

        # Configure thinking mode for GLM API
        # Primary flag recognized by Z.ai GLM API
        extra_body["thinking"] = {"type": "enabled" if use_thinking else "disabled"}

        # Keep compatibility hints for alternative backends (no-ops for GLM if ignored)
        if not use_thinking:
            extra_body["chat_template_kwargs"] = {"enable_thinking": False}
        else:
            extra_body["thinking_config"] = {
                "enabled": True,
                "budget": self.config.thinking_budget,
                "reflection": self.config.enable_reflection,
                "effort": self.config.reasoning_effort,
            }

        # Add tool configuration only when tools are present
        # If caller provided tool_choice, let the superclass/caller decision stand
        if tool_choice is None:
            # Detect whether any tools are actually present (either passed in or set by base class)
            has_tools = bool(tools)
            if not has_tools:
                if params.get("tools"):
                    has_tools = True
                elif isinstance(params.get("extra_body"), dict) and params["extra_body"].get("tools"):
                    has_tools = True
            # Only set tool_choice if tools exist to avoid provider 400 errors
            if has_tools:
                requested_tool_choice = self.config.tool_choice or "auto"
                if requested_tool_choice not in ("auto", "none", "required"):
                    requested_tool_choice = "auto"
                extra_body["tool_choice"] = requested_tool_choice

        # Add response format if specified
        if self.config.response_format:
            extra_body["response_format"] = self.config.response_format

        # Add safety settings
        extra_body["safety_settings"] = self.config.safety_settings

        # Ensure high context window and output limits when supported
        body = params.setdefault("extra_body", {})
        # Prefer no strict output limit if backend supports; otherwise rely on max_tokens set in ctor
        if "max_output_tokens" not in body:
            body["max_output_tokens"] = self.max_tokens
        # Expand input context when supported by provider
        if "max_input_tokens" not in body:
            body["max_input_tokens"] = 90000

        return params

    # --- Provider-specific parsing to preserve thinking content ---
    def parse_provider_response(self, response: Any, **kwargs) -> ModelResponse:
        """Parse provider response but preserve tool calls from the base parser.

        We enhance only the content to add or strip <thinking> tags while keeping
        tool-calling metadata intact.
        """
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

            # Try to extract provider thinking if base content lacks markers
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
        """Extract GLM thinking content from a message object or dict."""
        if message is None:
            return None
        # Possible field names for thinking content in GLM API response
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
        # Also detect embedded <thinking> tags in content
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

    def _parse_xml_tool_calls(self, content: str) -> tuple:
        """
        Parse GLM XML tool calls and return (tool_calls, cleaned_content).

        GLM streaming API returns tool calls in XML format:
        <tool_call>function_name
        <arg_key>param1</arg_key>
        <arg_value>value1</arg_value>
        </tool_call>

        This method converts them to OpenAI-style tool call objects with:
        1. XML normalization to handle GLM variations
        2. Robust parsing
        3. Validation of parsed tool calls

        Args:
            content: Response content that may contain XML tool calls

        Returns:
            Tuple of (list of tool_call dicts, content without XML)
        """
        import re
        from uuid import uuid4

        tool_calls = []

        try:
            # Step 1: Normalize XML to handle GLM's inconsistencies
            normalized_content = self._normalize_tool_xml(content)

            # Step 2: Pattern to find all <tool_call>...</tool_call> blocks
            tool_call_pattern = r'<tool_call>(.*?)</tool_call>'
            matches = re.findall(tool_call_pattern, normalized_content, re.DOTALL)

            if not matches:
                # No tool calls found after normalization
                return [], content

            for match in matches:
                try:
                    # Extract function name (first line after <tool_call>)
                    lines = match.strip().split('\n')
                    if not lines:
                        glm_logger.warning("Empty tool call block, skipping")
                        continue

                    function_name = lines[0].strip()

                    # Validation: function name must be non-empty
                    if not function_name:
                        glm_logger.warning("Tool call missing function name, skipping")
                        continue

                    # Parse arg_key/arg_value pairs
                    args_dict = {}
                    arg_pattern = r'<arg_key>(.*?)</arg_key>\s*<arg_value>(.*?)</arg_value>'
                    for key, value in re.findall(arg_pattern, match, re.DOTALL):
                        args_dict[key.strip()] = value.strip()

                    # Validation: arguments must be serializable to JSON
                    try:
                        args_json = json.dumps(args_dict)
                    except (TypeError, ValueError) as e:
                        glm_logger.warning(f"Tool call arguments not JSON serializable: {e}, skipping")
                        continue

                    # Create OpenAI-style tool call
                    tool_call = {
                        "id": str(uuid4()),
                        "type": "function",
                        "function": {
                            "name": function_name,
                            "arguments": args_json
                        }
                    }

                    # Final validation: ensure all required fields present
                    if tool_call.get("id") and tool_call.get("function", {}).get("name"):
                        tool_calls.append(tool_call)
                        glm_logger.debug(f"Parsed and validated XML tool call: {function_name} with args: {args_dict}")
                    else:
                        glm_logger.warning("Tool call missing required fields, skipping")

                except Exception as e:
                    glm_logger.warning(f"Error parsing individual tool call: {e}, skipping this call")
                    continue

            # Step 3: Remove XML tool calls from content
            cleaned_content = re.sub(tool_call_pattern, '', normalized_content, flags=re.DOTALL).strip()

            # If we parsed tool calls successfully, return them
            if tool_calls:
                glm_logger.info(f"Successfully parsed {len(tool_calls)} valid tool call(s)")
                return tool_calls, cleaned_content
            else:
                # No valid tool calls after parsing, return original content
                glm_logger.warning("No valid tool calls found after parsing")
                return [], content

        except Exception as e:
            # Critical error in parsing logic - log and return empty to prevent crash
            glm_logger.error(f"Critical error in _parse_xml_tool_calls: {e}", exc_info=True)
            return [], content



    def _normalize_tool_xml(self, content: str) -> str:
        """
        Normalize GLM's inconsistent tool XML format to standard format.
        
        GLM sometimes emits variations like:
        - <tool> instead of <tool_call>
        - Extra whitespace: < tool_call>
        - Newlines: <tool\n
        
        This method repairs these issues before parsing.
        
        Args:
            content: Raw XML content from GLM
            
        Returns:
            Normalized XML content
        """
        import re

        # Fix <tool> or <tool\n or <tool whitespace> to <tool_call>
        content = re.sub(r'<tool\s+', '<tool_call>', content)
        content = re.sub(r'<tool\n', '<tool_call>\n', content)
        content = re.sub(r'<tool>', '<tool_call>', content)

        # Fix closing tags
        content = re.sub(r'</tool\s*>', '</tool_call>', content)
        content = re.sub(r'</tool\n', '</tool_call>\n', content)

        # Fix extra whitespace in opening tag
        content = re.sub(r'<\s+tool_call>', '<tool_call>', content)
        content = re.sub(r'<tool_call\s+>', '<tool_call>', content)

        return content

    def _attach_tool_calls_to_response(
        self,
        response: Optional[ModelResponse],
        source: str = "Invoke",
    ) -> None:
        """
        Detect GLM tool-call XML in a synchronous response and convert it to
        OpenAI-style tool_calls so Agno can execute the referenced tools.
        """
        if response is None:
            return

        # Respect native tool calls if provider already supplied them
        if getattr(response, "tool_calls", None):
            return

        content = getattr(response, "content", None)
        if not isinstance(content, str):
            return

        if not self.is_tool_call_xml(content):
            return

        tool_calls, cleaned_content = self._parse_xml_tool_calls(content)
        if not tool_calls:
            return

        response.tool_calls = tool_calls
        response.content = cleaned_content if cleaned_content else None
        glm_logger.info(
            f"[GLM {source}] Converted {len(tool_calls)} XML tool call(s) to OpenAI format"
        )

    def is_tool_call_xml(self, buffer: str) -> bool:
        """
        Quick check if buffer contains tool call XML markers.

        Checks for:
        - 'tool_call' (primary tag)
        - 'arg_key' / 'arg_value' (argument tags)

        Args:
            buffer: Content buffer to inspect

        Returns:
            True if buffer likely contains tool call XML
        """
        if not buffer:
            return False
        tool_markers = ['tool_call', 'arg_key', 'arg_value']
        return any(marker in buffer.lower() for marker in tool_markers)

    def is_thinking_tag_xml(self, buffer: str) -> bool:
        """
        Quick check if buffer contains thinking tag XML markers.

        Checks for:
        - Any partial or complete thinking tag patterns
        - Includes: '<think', '</think', 'thinking', '<|think'

        This is intentionally BROAD to catch partial tags like '</think' or '<think'
        that would be incomplete and should be discarded.

        Args:
            buffer: Content buffer to inspect

        Returns:
            True if buffer likely contains thinking tag XML
        """
        if not buffer:
            return False

        buffer_lower = buffer.lower()

        # Broad patterns to catch both complete and incomplete thinking tags
        thinking_patterns = [
            '<think',      # Catches <thinking>, <think>, </thinking>, </think>
            'think>',      # Catches thinking>, think>
            '<|think',     # Catches <|thinking|>, <|endofthinking|>
            'think|>',     # Catches thinking|>, endofthinking|>
        ]

        return any(pattern in buffer_lower for pattern in thinking_patterns)

    def _is_complete_tag(self, buffer: str) -> bool:
        """
        Check if buffer contains a complete XML tag.

        A complete tag is one that:
        - Starts with '<'
        - Ends with '>'
        - Is a KNOWN complete tag (not a truncated tag)

        Strategy: Be conservative - only return True for tags we KNOW are complete.
        Partial tags like '</think' or '</think>' will continue buffering.

        Args:
            buffer: Content buffer to inspect

        Returns:
            True if buffer contains a complete tag we recognize
        """
        if not buffer or not buffer.endswith('>'):
            return False

        # Strip whitespace for comparison
        stripped = buffer.strip()

        # STRICT CHECK: Only recognize KNOWN complete XML tags
        # NOTE: GLM internal markers (<|thinking|>, <|endofthinking|>) are handled
        # at chunk level preprocessing, NOT in circuit breaker
        known_complete_tags = [
            '<thinking>',
            '</thinking>',
        ]

        # Check if it exactly matches a known complete tag
        if stripped in known_complete_tags:
            return True

        # For tool_call tags, we need to check if it's a complete structure
        # A complete tool_call has both opening and closing tags
        if '<tool_call>' in stripped and '</tool_call>' in stripped:
            return True

        # IMPORTANT: Do NOT assume arbitrary <...> is complete
        # This prevents treating </think> as complete when it's actually truncated
        # We'll keep buffering until timeout or we get a known tag

        return False

    def _identify_tag_type(self, buffer: str) -> str:
        """
        Identify the type of XML tag in the buffer.
        
        Args:
            buffer: Content buffer containing a tag
            
        Returns:
            Tag type: 'thinking_open', 'thinking_close', 'tool_call', or 'unknown'
        """
        stripped = buffer.strip()

        # Check for thinking tags (XML format only)
        # GLM internal markers handled at chunk level, not here
        if stripped == '<thinking>':
            return 'thinking_open'

        if stripped == '</thinking>':
            return 'thinking_close'

        # Check for tool call tag
        if '<tool_call>' in stripped or '<tool>' in stripped:
            return 'tool_call'

        # Unknown tag type
        return 'unknown'

    def create_content_chunk(self, content: str, chunk_id: str = None,
                            model: str = None) -> ModelResponse:
        """
        Create a content-only chunk in Agno v2 format.

        Args:
            content: Text content to include in chunk
            chunk_id: Optional chunk ID (deprecated in v2, kept for compatibility)
            model: Optional model name (deprecated in v2, kept for compatibility)

        Returns:
            ModelResponse with content
        """
        # v2 API: Return ModelResponse directly instead of ChatCompletionChunk
        return ModelResponse(
            content=content,
            role="assistant",
            event="AssistantResponse",
        )

    def create_tool_call_chunk(self, tool_calls: List[Dict]) -> ModelResponse:
        """
        Create a chunk with tool calls in Agno v2 format.

        Args:
            tool_calls: List of tool call dicts (with id, type, function)

        Returns:
            ModelResponse with tool_calls as ChoiceDeltaToolCall objects
        """
        from openai.types.chat.chat_completion_chunk import (
            ChoiceDeltaToolCall,
            ChoiceDeltaToolCallFunction
        )
        
        # v2 API: Convert dicts to ChoiceDeltaToolCall objects
        # This is required because Agno's parse_tool_calls expects objects with .index attribute
        tool_call_objects = []
        for idx, tc in enumerate(tool_calls):
            tool_call_obj = ChoiceDeltaToolCall(
                index=idx,
                id=tc.get("id"),
                type=tc.get("type", "function"),
                function=ChoiceDeltaToolCallFunction(
                    name=tc["function"]["name"],
                    arguments=tc["function"]["arguments"]
                )
            )
            tool_call_objects.append(tool_call_obj)
        
        return ModelResponse(
            role="assistant",
            tool_calls=tool_call_objects,
            event="AssistantResponse",
        )

    def _sanitize_stream_text(self, text: str, use_thinking: bool) -> str:
        """Normalize GLM thinking markers and optionally strip thinking when disabled.

        - Replace abbreviated tags <think>/<\think> with normalized <thinking>/<\thinking>
        - If use_thinking is False: remove any thinking blocks and residual markers
        """
        try:
            if not isinstance(text, str) or not text:
                return text
            # Normalize abbreviated tags
            sanitized = text.replace('<think>', '<thinking>').replace('</think>', '</thinking>')
            if not use_thinking:
                # Remove any thinking blocks entirely
                stripped = self._strip_thinking_from_text(sanitized)
                return stripped if stripped is not None else sanitized
            return sanitized
        except Exception:
            return text

    def parse_provider_response_delta(self, response_delta: Any) -> ModelResponse:
        """
        Parse streaming response delta and convert XML tool calls to proper format.

        GLM's streaming API returns tool calls in XML format, which needs to be
        converted to OpenAI-style tool_call objects for agno to execute them.

        Args:
            response_delta: Streaming chunk from GLM API

        Returns:
            ModelResponse with proper tool_calls format
        """
        try:
            # Get base parsing from parent (OpenAILike)
            model_response = super().parse_provider_response_delta(response_delta)

            # Convert XML tool calls (if any) into OpenAI tool_calls
            self._attach_tool_calls_to_response(model_response, source="StreamChunk")

            # Minimal sanitizer to normalize abbreviated think tags even if base path leaks them
            try:
                if model_response.content and isinstance(model_response.content, str):
                    model_response.content = model_response.content.replace('<think>', '<thinking>').replace('</think>', '</thinking>')
            except Exception:
                pass
            return model_response

        except Exception as e:
            glm_logger.error(f"Error parsing GLM streaming response delta: {e}")
            return ModelResponse(content="")

    async def ainvoke_stream(
        self,
        messages: List[Message],
        assistant_message: Message,  # v2 API: required parameter
        response_format: Optional[Union[Dict, Type[BaseModel]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        run_response: Optional[Any] = None,  # v2 API: optional run context
    ):
        """
        REFACTORED BULLETPROOF streaming for GLM thinking mode and tool calls.

        New Architecture:
        - Unified single buffer (no duplicate buffering layers)
        - Chunk-level regex processing (no char-by-char loops)
        - State machine for thinking blocks
        - Progressive parsing (parse complete structures immediately)
        - Content preservation (never discard)
        - End-to-end validation

        Args:
            messages: Conversation messages
            assistant_message: Assistant message object for response (v2 API required)
            response_format: Response format specification
            tools: Available tools
            tool_choice: Tool selection strategy
            run_response: Optional run context for team/agent runs (v2 API)

        Yields:
            ChatCompletionChunk objects with tool_calls in OpenAI format and proper thinking tags
        """
        import re
        from enum import Enum

        # State machine for thinking processing
        class ThinkingState(Enum):
            OUTSIDE = "outside"  # Not in thinking block
            INSIDE = "inside"    # Inside thinking block
            BUFFERING = "buffering"  # Accumulating potential tags

        # Initialize state
        state = ThinkingState.OUTSIDE
        unified_buffer = ""  # Single buffer for all content
        thinking_opened = False
        tool_calls_sent = False

        # ═══════════════════════════════════════════════════════════════
        # CRITICAL: Clear flag BEFORE determining thinking mode (Fix 3)
        # This ensures no state leakage between requests
        # ═══════════════════════════════════════════════════════════════
        self._use_thinking_for_next_request = None
        
        # Determine if thinking mode is enabled for this request (opt-in principle)
        use_thinking = self._should_use_thinking(messages)
        self._use_thinking_for_next_request = use_thinking
        
        glm_logger.debug(
            f"[GLM Stream] Thinking mode decision: {use_thinking} "
            f"(client_thinking_type={self.client_thinking_type}, mode={self.mode.value})"
        )

        # Streaming metrics
        import time
        stream_start_time = time.time()
        chunk_count = 0
        total_bytes = 0

        # Log streaming session start
        glm_logger.info(f"🚀 [GLM Stream] SESSION START - Model: {self.id}, Mode: {self.mode.value}, Thinking: {use_thinking}")

        # DYNAMIC MAX_TOKENS CALCULATION
        # Calculate input tokens and adjust max_tokens to prevent context overflow
        estimated_input_tokens = self._estimate_message_tokens(messages)
        
        # Apply estimation safety margin to account for discrepancies
        # (system prompts, tool definitions, formatting overhead, etc.)
        adjusted_input_tokens = estimated_input_tokens + self.estimation_safety_margin
        
        # Calculate available tokens using API context limit (more accurate)
        # This ensures we respect the actual API limits, not just our safe limit
        available_tokens_api = self.api_context_limit - adjusted_input_tokens - self.context_safety_buffer
        
        # Also calculate using safe limit for comparison
        available_tokens_safe = self.safe_output_limit - adjusted_input_tokens - self.context_safety_buffer
        
        # Store original max_tokens to restore later
        original_max_tokens = self.max_tokens
        
        # Use the more restrictive limit (API limit vs safe limit)
        # This ensures we never exceed what the API actually supports
        available_tokens = min(available_tokens_api, available_tokens_safe)
        
        # Edge case handling for critically large inputs
        if available_tokens <= 0:
            # Input exceeds context limit - calculate absolute minimum
            # Use API context limit directly (most accurate)
            absolute_max_available = max(0, self.api_context_limit - adjusted_input_tokens)
            
            if adjusted_input_tokens >= self.api_context_limit:
                glm_logger.error(
                    f"❌ [GLM Token Budget] Input tokens ({estimated_input_tokens} + {self.estimation_safety_margin} margin = {adjusted_input_tokens}) "
                    f"exceed API context limit ({self.api_context_limit})! "
                    f"This request will likely fail."
                )
                # Set to absolute minimum (1 token) - request may still fail but we try
                adjusted_max_tokens = 1
            else:
                glm_logger.warning(
                    f"⚠️ [GLM Token Budget] Critical: Input tokens ({estimated_input_tokens} + {self.estimation_safety_margin} margin = {adjusted_input_tokens}) "
                    f"leave only {absolute_max_available} tokens available. "
                    f"API limit: {self.api_context_limit}, Setting max_tokens to {absolute_max_available}"
                )
                adjusted_max_tokens = absolute_max_available
        elif available_tokens < 100:
            # Very limited space - use exact calculation
            absolute_max_available = max(0, self.api_context_limit - adjusted_input_tokens)
            glm_logger.warning(
                f"⚠️ [GLM Token Budget] Very limited output space. "
                f"Estimated input: {estimated_input_tokens} (+ {self.estimation_safety_margin} margin = {adjusted_input_tokens}), "
                f"Available: {available_tokens}, API limit: {self.api_context_limit}, "
                f"Setting max_tokens to {absolute_max_available}"
            )
            adjusted_max_tokens = absolute_max_available
        else:
            # Normal case: adjust max_tokens to fit within available space
            adjusted_max_tokens = min(original_max_tokens, available_tokens)
        
        # Final safety check: ensure max_tokens never exceeds what's actually available
        # This is a hard limit based on API context window
        absolute_max = max(0, self.api_context_limit - adjusted_input_tokens)
        if adjusted_max_tokens > absolute_max:
            glm_logger.warning(
                f"⚠️ [GLM Token Budget] Clamping max_tokens from {adjusted_max_tokens} to {absolute_max} "
                f"based on API context limit ({self.api_context_limit} - {adjusted_input_tokens} input)"
            )
            adjusted_max_tokens = absolute_max
        
        # Apply the adjusted max_tokens
        self.max_tokens = adjusted_max_tokens
        
        # Log token budget calculation
        if adjusted_max_tokens < original_max_tokens:
            reduction_pct = ((original_max_tokens - adjusted_max_tokens) / original_max_tokens) * 100
            if reduction_pct > 50:
                glm_logger.warning(
                    f"⚠️ [GLM Token Budget] Significant reduction: "
                    f"Estimated input: {estimated_input_tokens} (+ {self.estimation_safety_margin} margin = {adjusted_input_tokens}), "
                    f"Available: {available_tokens}, API limit: {self.api_context_limit}, "
                    f"Adjusted max_tokens: {adjusted_max_tokens} "
                    f"(from {original_max_tokens}, {reduction_pct:.1f}% reduction)"
                )
            else:
                glm_logger.info(
                    f"📊 [GLM Token Budget] Estimated input: {estimated_input_tokens} (+ {self.estimation_safety_margin} margin = {adjusted_input_tokens}), "
                    f"Available: {available_tokens}, Adjusted max_tokens: {adjusted_max_tokens} (from {original_max_tokens})"
                )
        else:
            glm_logger.info(
                f"📊 [GLM Token Budget] Estimated input: {estimated_input_tokens} (+ {self.estimation_safety_margin} margin = {adjusted_input_tokens}), "
                f"Available: {available_tokens}, API limit: {self.api_context_limit}, "
                f"Using full max_tokens: {adjusted_max_tokens}"
            )

        # Regex patterns for chunk-level processing
        # CRITICAL: Match ALL variations including abbreviated forms
        GLM_THINKING_OPEN = re.compile(r'<\|thinking\|>|<thinking>|<think>')
        GLM_THINKING_CLOSE = re.compile(r'<\|endofthinking\|>|</thinking>|</think>')
        TOOL_CALL_COMPLETE = re.compile(r'<tool_call>.*?</tool_call>', re.DOTALL)

        try:
            # Get parent's async stream with adjusted max_tokens
            # v2 API: pass all required parameters explicitly
            parent_stream = super().ainvoke_stream(
                messages=messages,
                assistant_message=assistant_message,
                response_format=response_format,
                tools=tools,
                tool_choice=tool_choice,
                run_response=run_response,
            )

            # Streaming safety thresholds (env-tunable)
            import os as _os
            try:
                flush_threshold = int(_os.getenv("GLM_STREAM_FLUSH_THRESHOLD", "32768"))
            except Exception:
                flush_threshold = 32768
            try:
                tag_lookahead = int(_os.getenv("GLM_STREAM_TAG_LOOKAHEAD", "256"))
            except Exception:
                tag_lookahead = 256

            # Reorder so first visible output starts with <thinking>
            preamble_before_first_thinking = ""
            first_thinking_seen = False

            async for chunk in parent_stream:
                # v2 API: ModelResponse has content directly (no choices/delta structure)
                # If chunk has no content and no tool_calls, skip it
                if chunk.content is None and not chunk.tool_calls:
                    yield chunk
                    continue

                # If chunk already has native tool_calls, pass through
                if chunk.tool_calls:
                    glm_logger.debug("Native tool_calls detected, passing through")
                    # Flush any buffered content first
                    if unified_buffer:
                        yield ModelResponse(
                            content=self._sanitize_stream_text(unified_buffer, use_thinking),
                            event=chunk.event,
                        )
                        unified_buffer = ""
                    yield chunk
                    tool_calls_sent = True
                    continue

                # If no content, pass through
                if chunk.content is None:
                    yield chunk
                    continue

                content = chunk.content
                unified_buffer += content
                chunk_count += 1
                total_bytes += len(content)

                # ═══════════════════════════════════════════════════════════════
                # PROGRESSIVE PARSING: Process complete structures immediately
                # ═══════════════════════════════════════════════════════════════

                while unified_buffer:
                    processed = False

                    # Debug: Log buffer state
                    glm_logger.debug(f"[GLM Stream] Buffer size: {len(unified_buffer)}, State: {state.value}, Use thinking: {use_thinking}")

                    # 1. Check for complete tool calls
                    if not tool_calls_sent:
                        tool_match = TOOL_CALL_COMPLETE.search(unified_buffer)
                        if tool_match:
                            glm_logger.info("[GLM Stream] Tool call XML detected in buffer")
                            # Extract and parse tool call
                            before_tool = unified_buffer[:tool_match.start()]
                            tool_xml = tool_match.group(0)
                            after_tool = unified_buffer[tool_match.end():]

                            # Send content before tool call
                            if before_tool:
                                glm_logger.debug(f"[GLM Stream] Sending {len(before_tool)} chars before tool call")
                                yield self.create_content_chunk(
                                    self._sanitize_stream_text(before_tool, use_thinking),
                                )

                            # Parse and send tool call
                            tool_calls_list, _ = self._parse_xml_tool_calls(tool_xml)
                            if tool_calls_list:
                                glm_logger.info(f"[GLM Stream] ✅ Parsed {len(tool_calls_list)} tool calls successfully")
                                yield self.create_tool_call_chunk(tool_calls_list)
                                tool_calls_sent = True
                            else:
                                glm_logger.warning("[GLM Stream] ⚠️ Tool call parsing failed, treating as text")

                            # Continue with remaining content
                            unified_buffer = after_tool
                            processed = True
                            continue

                    # 2a. Handle stray closing tag while OUTSIDE (drop it, preserve surrounding text)
                    if state == ThinkingState.OUTSIDE:
                        stray_close = GLM_THINKING_CLOSE.search(unified_buffer)
                        open_probe = GLM_THINKING_OPEN.search(unified_buffer)
                        if stray_close and (open_probe is None or stray_close.start() < open_probe.start()):
                            before_close = unified_buffer[:stray_close.start()]
                            after_close = unified_buffer[stray_close.end():]
                            if before_close:
                                # If we have not yet emitted the first thinking block, buffer any
                                # preamble text so the very first visible chunk remains the opening
                                # <thinking> tag. This avoids leading fragments like "ce with.".
                                if not first_thinking_seen:
                                    preamble_before_first_thinking += before_close
                                else:
                                    yield self.create_content_chunk(self._sanitize_stream_text(before_close, use_thinking))
                            unified_buffer = after_close
                            processed = True
                            continue

                    # 2. Check for thinking opening tag
                    if use_thinking and state == ThinkingState.OUTSIDE:
                        open_match = GLM_THINKING_OPEN.search(unified_buffer)
                        if open_match:
                            glm_logger.info(f"[GLM Stream] 🧠 Thinking opening tag detected (matched: '{open_match.group(0)}')")
                            # Send content before thinking tag
                            before_tag = unified_buffer[:open_match.start()]
                            if before_tag:
                                if not first_thinking_seen:
                                    preamble_before_first_thinking += before_tag
                                    glm_logger.debug(f"[GLM Stream] Buffered {len(before_tag)} chars preamble before first thinking tag")
                                else:
                                    glm_logger.debug(f"[GLM Stream] Sending {len(before_tag)} chars before thinking tag")
                                    yield self.create_content_chunk(self._sanitize_stream_text(before_tag, use_thinking))

                            # Send opening tag atomically
                            yield self.create_content_chunk("<thinking>\n")
                            first_thinking_seen = True
                            thinking_opened = True
                            state = ThinkingState.INSIDE
                            glm_logger.info(f"[GLM Stream] ✅ Entered thinking block - State: {state.value}")

                            # Continue with content after tag
                            unified_buffer = unified_buffer[open_match.end():]
                            processed = True
                            continue

                    # 3. Check for thinking closing tag
                    if use_thinking and state == ThinkingState.INSIDE:
                        close_match = GLM_THINKING_CLOSE.search(unified_buffer)
                        if close_match:
                            glm_logger.info(f"[GLM Stream] 🧠 Thinking closing tag detected (matched: '{close_match.group(0)}')")
                            # Send thinking content before closing tag
                            thinking_content = unified_buffer[:close_match.start()]
                            if thinking_content:
                                glm_logger.debug(f"[GLM Stream] Sending {len(thinking_content)} chars of thinking content")
                                yield self.create_content_chunk(thinking_content)

                            # Send closing tag atomically
                            yield self.create_content_chunk("\n</thinking>\n\n")
                            # If we have held back a preamble for the first block, emit it now
                            if preamble_before_first_thinking:
                                glm_logger.debug(f"[GLM Stream] Emitting buffered preamble of {len(preamble_before_first_thinking)} chars after first thinking block")
                                yield self.create_content_chunk(preamble_before_first_thinking)
                                preamble_before_first_thinking = ""
                            thinking_opened = False
                            state = ThinkingState.OUTSIDE
                            glm_logger.info(f"[GLM Stream] ✅ Exited thinking block - State: {state.value}")

                            # Continue with content after tag
                            unified_buffer = unified_buffer[close_match.end():]
                            processed = True
                            continue

                    # 4. If no complete structures found, check if we should flush buffer
                    if not processed:
                        # Check if buffer is getting too large (safety valve)
                        if len(unified_buffer) > flush_threshold:
                            glm_logger.warning(f"[GLM Stream] Buffer size exceeded {flush_threshold} chars ({len(unified_buffer)}), applying safety flush")

                            # CRITICAL: Check if buffer contains potential tag markers
                            # Don't flush if we might be about to receive a tag
                            contains_tag_start = '<' in unified_buffer[-tag_lookahead:]  # Check tail for '<'

                            if contains_tag_start:
                                # Potential tag marker detected - only flush content BEFORE the last '<'
                                last_bracket_pos = unified_buffer.rfind('<')
                                if last_bracket_pos > 0:
                                    flush_content = unified_buffer[:last_bracket_pos]
                                    if flush_content and state == ThinkingState.OUTSIDE:
                                        # Only flush if we're not in thinking mode
                                        yield self.create_content_chunk(self._sanitize_stream_text(flush_content, use_thinking))
                                        unified_buffer = unified_buffer[last_bracket_pos:]
                                        glm_logger.warning(f"[GLM Stream] ⚠️ Tag marker detected - flushed {len(flush_content)} chars, kept {len(unified_buffer)} for tag detection")
                                    elif flush_content and state == ThinkingState.INSIDE:
                                        # In thinking mode - send as thinking content
                                        yield self.create_content_chunk(flush_content)
                                        unified_buffer = unified_buffer[last_bracket_pos:]
                                        glm_logger.debug(f"[GLM Stream] Thinking mode - flushed {len(flush_content)} chars, kept {len(unified_buffer)}")
                            else:
                                # No tag markers - safe to flush, keep last tag_lookahead chars for tag detection
                                flush_content = unified_buffer[:-tag_lookahead]
                                if flush_content:
                                    yield self.create_content_chunk(self._sanitize_stream_text(flush_content, use_thinking))
                                    unified_buffer = unified_buffer[-tag_lookahead:]
                                    glm_logger.debug(f"[GLM Stream] Normal buffer flush: {len(flush_content)} chars (kept {len(unified_buffer)} for tag detection)")
                        break  # Wait for more chunks

            # Stream ended - process remaining buffer through tag detection
            # CRITICAL: Never send raw GLM tags - always convert them
            if unified_buffer:
                glm_logger.info(f"[GLM Stream] Stream ended with {len(unified_buffer)} chars in buffer - processing tags")

                # Process buffer through same tag detection logic used during streaming
                while unified_buffer:
                    processed_at_end = False

                    # 0. Drop any stray closing tags if OUTSIDE
                    if state == ThinkingState.OUTSIDE:
                        stray_close = GLM_THINKING_CLOSE.search(unified_buffer)
                        open_probe = GLM_THINKING_OPEN.search(unified_buffer)
                        if stray_close and (open_probe is None or stray_close.start() < open_probe.start()):
                            before_close = unified_buffer[:stray_close.start()]
                            after_close = unified_buffer[stray_close.end():]
                            if before_close:
                                # At stream end, if we never saw an opening tag, just emit the
                                # sanitized text; otherwise, preserve ordering by buffering.
                                if not first_thinking_seen:
                                    yield self.create_content_chunk(self._sanitize_stream_text(before_close, use_thinking))
                                else:
                                    preamble_before_first_thinking += before_close
                            unified_buffer = after_close
                            processed_at_end = True
                            continue

                    # 1. Check for thinking opening tag
                    if use_thinking and state == ThinkingState.OUTSIDE:
                        open_match = GLM_THINKING_OPEN.search(unified_buffer)
                        if open_match:
                            glm_logger.info(f"[GLM Stream] 🧠 Stream-end: Opening tag detected (matched: '{open_match.group(0)}')")
                            # Send content before thinking tag
                            before_tag = unified_buffer[:open_match.start()]
                            if before_tag:
                                glm_logger.debug(f"[GLM Stream] Stream-end: Sending {len(before_tag)} chars before opening tag")
                                yield self.create_content_chunk(self._sanitize_stream_text(before_tag, use_thinking))

                            # Send opening tag atomically (converted)
                            yield self.create_content_chunk("<thinking>\n")
                            thinking_opened = True
                            state = ThinkingState.INSIDE
                            glm_logger.info("[GLM Stream] ✅ Stream-end: Entered thinking block")

                            # Continue with content after tag
                            unified_buffer = unified_buffer[open_match.end():]
                            processed_at_end = True
                            continue

                    # 2. Check for thinking closing tag
                    if use_thinking and state == ThinkingState.INSIDE:
                        close_match = GLM_THINKING_CLOSE.search(unified_buffer)
                        if close_match:
                            glm_logger.info(f"[GLM Stream] 🧠 Stream-end: Closing tag detected (matched: '{close_match.group(0)}')")
                            # Send thinking content before closing tag
                            thinking_content = unified_buffer[:close_match.start()]
                            if thinking_content:
                                glm_logger.debug(f"[GLM Stream] Stream-end: Sending {len(thinking_content)} chars of thinking content")
                                yield self.create_content_chunk(thinking_content)

                            # Send closing tag atomically (converted)
                            yield self.create_content_chunk("\n</thinking>\n\n")
                            thinking_opened = False
                            state = ThinkingState.OUTSIDE
                            glm_logger.info("[GLM Stream] ✅ Stream-end: Exited thinking block")

                            # Continue with content after tag
                            unified_buffer = unified_buffer[close_match.end():]
                            processed_at_end = True
                            continue

                    # 3. No more tags found - send remaining content
                    if not processed_at_end:
                        # Check for incomplete tag fragments that should be discarded
                        stripped = unified_buffer.strip()
                        is_incomplete = (
                            (stripped.startswith('<') and not stripped.endswith('>') and len(stripped) < 30) or
                            (stripped.endswith('<') or stripped.endswith('</'))
                        )

                        if is_incomplete and len(stripped) < 30:
                            glm_logger.warning(f"[GLM Stream] ⚠️ Stream-end: Discarding incomplete tag fragment: {repr(stripped[:50])}")
                        else:
                            glm_logger.info(f"[GLM Stream] Stream-end: Sending final {len(unified_buffer)} chars")
                            yield self.create_content_chunk(self._sanitize_stream_text(unified_buffer, use_thinking))

                        break  # Done processing

            # Final validation
            if thinking_opened and use_thinking:
                glm_logger.error("[GLM Stream] ❌ VALIDATION ERROR: Thinking block was opened but never closed!")
                glm_logger.error("[GLM Stream] This indicates incomplete response - thinking content may be truncated")
            else:
                glm_logger.info(f"[GLM Stream] ✅ Stream completed successfully - State: {state.value}, Thinking opened: {thinking_opened}")

        except Exception as e:
            stream_duration = time.time() - stream_start_time
            glm_logger.error(f"❌ [GLM Stream] SESSION ERROR after {stream_duration:.2f}s - {chunk_count} chunks, {total_bytes} bytes: {e}", exc_info=True)
            raise
        finally:
            # Log streaming session end with metrics
            stream_duration = time.time() - stream_start_time
            glm_logger.info(f"✅ [GLM Stream] SESSION END - Duration: {stream_duration:.2f}s, Chunks: {chunk_count}, Bytes: {total_bytes}, Throughput: {total_bytes/max(stream_duration, 0.001):.0f} bytes/s")

            # Restore original max_tokens after streaming
            self.max_tokens = original_max_tokens
            
            # Clear the flag after stream completes
            self._use_thinking_for_next_request = None

    def _is_retryable_error(self, error: Exception) -> bool:
        """Return True if the error looks retryable (rate limits/transient network)."""
        try:
            message = str(error) if error else ""
            lowered = message.lower()
            # Common retryable signals: rate limit and transient server/network errors
            retry_signals = [
                "429", "too many requests", "rate limit", "timeout",
                "timed out", "connection reset", "service unavailable",
                "bad gateway", "gateway timeout", "temporary failure",
            ]
            return any(sig in lowered for sig in retry_signals)
        except Exception:
            return False

    def invoke(
        self,
        messages: List[Message],
        assistant_message: Message,  # v2 API: required parameter
        response_format: Optional[Union[Dict, Type[BaseModel]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        run_response: Optional[Any] = None,  # v2 API: optional run context
    ) -> ModelResponse:
        """
        Invoke GLM4.5 model with thinking mode support
        
        Args:
            messages: Conversation messages
            assistant_message: Assistant message object for response (v2 API required)
            response_format: Response format specification
            tools: Available tools
            tool_choice: Tool selection strategy
            run_response: Optional run context for team/agent runs (v2 API)
            
        Returns:
            ModelResponse object
        """
        start_time = time.time()

        # ═══════════════════════════════════════════════════════════════
        # CRITICAL: Clear flag BEFORE determining thinking mode (Fix 3)
        # This ensures no state leakage between requests
        # ═══════════════════════════════════════════════════════════════
        self._use_thinking_for_next_request = None

        # ---------- Dynamic max_tokens calculation (non-streaming) ----------
        # Estimate input tokens and adjust max_tokens to avoid context overflow
        try:
            estimated_input_tokens = self._estimate_message_tokens(messages)
        except Exception:
            # Fallback if estimation fails
            estimated_input_tokens = 0
        adjusted_input_tokens = estimated_input_tokens + self.estimation_safety_margin
        # Compute available tokens using API context limit and safe output limit
        available_tokens_api = self.api_context_limit - adjusted_input_tokens - self.context_safety_buffer
        available_tokens_safe = self.safe_output_limit - adjusted_input_tokens - self.context_safety_buffer
        original_max_tokens = self.max_tokens
        # Pick the stricter budget
        available_tokens = min(available_tokens_api, available_tokens_safe)
        # Edge handling
        if available_tokens <= 0:
            # Absolute max available solely from API limit (may still be 0)
            absolute_max_available = max(0, self.api_context_limit - adjusted_input_tokens)
            adjusted_max_tokens = 1 if adjusted_input_tokens >= self.api_context_limit else absolute_max_available
            glm_logger.warning(
                f"⚠️ [GLM Token Budget] Non-stream: very limited or no space. "
                f"Estimated input: {estimated_input_tokens} (+ {self.estimation_safety_margin} margin = {adjusted_input_tokens}), "
                f"Setting max_tokens to {adjusted_max_tokens}"
            )
        else:
            adjusted_max_tokens = min(original_max_tokens, available_tokens)
        # Final clamp to absolute API context window
        absolute_max = max(0, self.api_context_limit - adjusted_input_tokens)
        if adjusted_max_tokens > absolute_max:
            glm_logger.warning(
                f"⚠️ [GLM Token Budget] Non-stream: clamping max_tokens from {adjusted_max_tokens} to {absolute_max} "
                f"based on API context limit ({self.api_context_limit} - {adjusted_input_tokens} input)"
            )
            adjusted_max_tokens = absolute_max
        # Apply adjusted max_tokens
        self.max_tokens = adjusted_max_tokens
        # ---------- End dynamic max_tokens calculation ----------

        # Preprocess messages (Arabic optimization) in-place
        if self.config.arabic_optimization:
            for msg in messages:
                if isinstance(msg.content, str) and self._contains_arabic(msg.content):
                    msg.content = self._preprocess_arabic(msg.content)

        # Determine mode for this request and set flag (opt-in principle)
        use_thinking = self._should_use_thinking(messages)
        self._use_thinking_for_next_request = use_thinking
        
        glm_logger.debug(
            f"[GLM Invoke] Thinking mode decision: {use_thinking} "
            f"(client_thinking_type={self.client_thinking_type}, mode={self.mode.value})"
        )

        attempt = 0
        while True:
            try:
                # Call parent invoke method (it will call our get_request_params)
                # v2 API: pass all required parameters explicitly
                response = super().invoke(
                    messages=messages,
                    assistant_message=assistant_message,
                    response_format=response_format,
                    tools=tools,
                    tool_choice=tool_choice,
                    run_response=run_response,
                )

                # Reformat content to expose thinking in <thinking> tags when available
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
                            # Strip any thinking content if model unexpectedly returned it
                            stripped = self._strip_thinking_from_text(response.content)
                            if stripped is not None:
                                response.content = stripped
                except Exception:
                    pass

                # Track thinking metrics if applicable (be defensive about usage type)
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

                # Non-stream responses can also contain XML tool call payloads; convert them.
                self._attach_tool_calls_to_response(response, source="Invoke")

                return response
            except Exception as e:
                attempt += 1
                # Decide whether to retry
                should_retry = attempt <= self.max_retries and self._is_retryable_error(e)
                if not should_retry:
                    glm_logger.error(f"Error invoking GLM4.5: {str(e)}")
                    raise
                # Exponential backoff starting at the configured initial delay
                delay_seconds = self.initial_retry_delay * (2 ** (attempt - 1))
                glm_logger.warning(
                    f"Invoke attempt {attempt} failed: {e}. Retrying in {delay_seconds:.2f}s "
                    f"({attempt}/{self.max_retries})"
                )
                time.sleep(delay_seconds)
            finally:
                # Clear the flag after the request attempt completes
                # (it will be set again on next loop iteration)
                self._use_thinking_for_next_request = None

    def invoke_stream(
        self,
        messages: List[Message],
        assistant_message: Message,  # v2 API: required parameter
        response_format: Optional[Union[Dict, Type[BaseModel]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        run_response: Optional[Any] = None,  # v2 API: optional run context
    ) -> Iterator[Union[str, ModelResponse]]:
        """
        REFACTORED sync streaming - matches ainvoke_stream architecture

        Args:
            messages: Conversation messages
            assistant_message: Assistant message object for response (v2 API required)
            response_format: Response format specification
            tools: Available tools
            tool_choice: Tool selection strategy
            run_response: Optional run context for team/agent runs (v2 API)

        Yields:
            Streamed response chunks
        """
        import re

        # ═══════════════════════════════════════════════════════════════
        # CRITICAL: Clear flag BEFORE determining thinking mode (Fix 3)
        # This ensures no state leakage between requests
        # ═══════════════════════════════════════════════════════════════
        self._use_thinking_for_next_request = None

        # Preprocess messages (Arabic optimization) in-place
        if self.config.arabic_optimization:
            for msg in messages:
                if isinstance(msg.content, str) and self._contains_arabic(msg.content):
                    msg.content = self._preprocess_arabic(msg.content)

        # Determine mode for this request and set flag (opt-in principle)
        use_thinking = self._should_use_thinking(messages)
        self._use_thinking_for_next_request = use_thinking
        
        glm_logger.debug(
            f"[GLM Invoke Stream] Thinking mode decision: {use_thinking} "
            f"(client_thinking_type={self.client_thinking_type}, mode={self.mode.value})"
        )

        # DYNAMIC MAX_TOKENS CALCULATION
        # Calculate input tokens and adjust max_tokens to prevent context overflow
        estimated_input_tokens = self._estimate_message_tokens(messages)
        
        # Apply estimation safety margin to account for discrepancies
        # (system prompts, tool definitions, formatting overhead, etc.)
        adjusted_input_tokens = estimated_input_tokens + self.estimation_safety_margin
        
        # Calculate available tokens using API context limit (more accurate)
        # This ensures we respect the actual API limits, not just our safe limit
        available_tokens_api = self.api_context_limit - adjusted_input_tokens - self.context_safety_buffer
        
        # Also calculate using safe limit for comparison
        available_tokens_safe = self.safe_output_limit - adjusted_input_tokens - self.context_safety_buffer
        
        # Store original max_tokens to restore later
        original_max_tokens = self.max_tokens
        
        # Use the more restrictive limit (API limit vs safe limit)
        # This ensures we never exceed what the API actually supports
        available_tokens = min(available_tokens_api, available_tokens_safe)
        
        # Edge case handling for critically large inputs
        if available_tokens <= 0:
            # Input exceeds context limit - calculate absolute minimum
            # Use API context limit directly (most accurate)
            absolute_max_available = max(0, self.api_context_limit - adjusted_input_tokens)
            
            if adjusted_input_tokens >= self.api_context_limit:
                glm_logger.error(
                    f"❌ [GLM Token Budget] Input tokens ({estimated_input_tokens} + {self.estimation_safety_margin} margin = {adjusted_input_tokens}) "
                    f"exceed API context limit ({self.api_context_limit})! "
                    f"This request will likely fail."
                )
                # Set to absolute minimum (1 token) - request may still fail but we try
                adjusted_max_tokens = 1
            else:
                glm_logger.warning(
                    f"⚠️ [GLM Token Budget] Critical: Input tokens ({estimated_input_tokens} + {self.estimation_safety_margin} margin = {adjusted_input_tokens}) "
                    f"leave only {absolute_max_available} tokens available. "
                    f"API limit: {self.api_context_limit}, Setting max_tokens to {absolute_max_available}"
                )
                adjusted_max_tokens = absolute_max_available
        elif available_tokens < 100:
            # Very limited space - use exact calculation
            absolute_max_available = max(0, self.api_context_limit - adjusted_input_tokens)
            glm_logger.warning(
                f"⚠️ [GLM Token Budget] Very limited output space. "
                f"Estimated input: {estimated_input_tokens} (+ {self.estimation_safety_margin} margin = {adjusted_input_tokens}), "
                f"Available: {available_tokens}, API limit: {self.api_context_limit}, "
                f"Setting max_tokens to {absolute_max_available}"
            )
            adjusted_max_tokens = absolute_max_available
        else:
            # Normal case: adjust max_tokens to fit within available space
            adjusted_max_tokens = min(original_max_tokens, available_tokens)
        
        # Final safety check: ensure max_tokens never exceeds what's actually available
        # This is a hard limit based on API context window
        absolute_max = max(0, self.api_context_limit - adjusted_input_tokens)
        if adjusted_max_tokens > absolute_max:
            glm_logger.warning(
                f"⚠️ [GLM Token Budget] Clamping max_tokens from {adjusted_max_tokens} to {absolute_max} "
                f"based on API context limit ({self.api_context_limit} - {adjusted_input_tokens} input)"
            )
            adjusted_max_tokens = absolute_max
        
        # Apply the adjusted max_tokens
        self.max_tokens = adjusted_max_tokens

        # Log token budget calculation
        if adjusted_max_tokens < original_max_tokens:
            reduction_pct = ((original_max_tokens - adjusted_max_tokens) / original_max_tokens) * 100
            if reduction_pct > 50:
                glm_logger.warning(
                    f"⚠️ [GLM Token Budget] Significant reduction: "
                    f"Estimated input: {estimated_input_tokens} (+ {self.estimation_safety_margin} margin = {adjusted_input_tokens}), "
                    f"Available: {available_tokens}, API limit: {self.api_context_limit}, "
                    f"Adjusted max_tokens: {adjusted_max_tokens} "
                    f"(from {original_max_tokens}, {reduction_pct:.1f}% reduction)"
                )
            else:
                glm_logger.info(
                    f"📊 [GLM Token Budget] Estimated input: {estimated_input_tokens} (+ {self.estimation_safety_margin} margin = {adjusted_input_tokens}), "
                    f"Available: {available_tokens}, Adjusted max_tokens: {adjusted_max_tokens} (from {original_max_tokens})"
                )
        else:
            glm_logger.info(
                f"✅ [GLM Token Budget] Estimated input: {estimated_input_tokens} (+ {self.estimation_safety_margin} margin = {adjusted_input_tokens}), "
                f"Max output: {adjusted_max_tokens}, API limit: {self.api_context_limit}, "
                f"Total budget: {adjusted_input_tokens + adjusted_max_tokens} / {self.api_context_limit}"
            )

        # Simple state tracking
        in_thinking = False
        unified_buffer = ""
        # Reordering support and thresholds for sync path
        first_thinking_seen = False
        preamble_before_first_thinking = ""
        import os as _os_sync
        try:
            flush_threshold = int(_os_sync.getenv("GLM_STREAM_FLUSH_THRESHOLD", "32768"))
        except Exception:
            flush_threshold = 32768
        try:
            tag_lookahead = int(_os_sync.getenv("GLM_STREAM_TAG_LOOKAHEAD", "256"))
        except Exception:
            tag_lookahead = 256

        # Regex patterns (same as async)
        # CRITICAL: Match ALL variations including abbreviated forms
        GLM_THINKING_OPEN = re.compile(r'<\|thinking\|>|<thinking>|<think>')
        GLM_THINKING_CLOSE = re.compile(r'<\|endofthinking\|>|</thinking>|</think>')

        attempt = 0
        yielded_any = False

        while True:
            try:
                # v2 API: pass all required parameters explicitly
                for raw_chunk in super().invoke_stream(
                    messages=messages,
                    assistant_message=assistant_message,
                    response_format=response_format,
                    tools=tools,
                    tool_choice=tool_choice,
                    run_response=run_response,
                ):
                    yielded_any = True

                    # Extract text content
                    chunk_text: Optional[str] = None
                    is_model_response = hasattr(raw_chunk, "content")
                    original_chunk = raw_chunk

                    if isinstance(raw_chunk, str):
                        chunk_text = raw_chunk
                    elif is_model_response and isinstance(getattr(raw_chunk, "content", None), str):
                        chunk_text = raw_chunk.content

                    if chunk_text is None:
                        yield original_chunk
                        continue

                    unified_buffer += chunk_text

                    # Process complete thinking blocks
                    while unified_buffer:
                        processed = False

                        # Check for opening tag
                        if use_thinking and not in_thinking:
                            open_match = GLM_THINKING_OPEN.search(unified_buffer)
                            if open_match:
                                # Send content before tag
                                before = unified_buffer[:open_match.start()]
                                if before:
                                    if not first_thinking_seen:
                                        preamble_before_first_thinking += before
                                    else:
                                        yield ModelResponse(content=self._sanitize_stream_text(before, use_thinking))

                                # Send opening tag
                                yield ModelResponse(content="<thinking>\n")
                                in_thinking = True
                                first_thinking_seen = True

                                unified_buffer = unified_buffer[open_match.end():]
                                processed = True
                                continue

                        # Check for closing tag
                        if use_thinking and in_thinking:
                            close_match = GLM_THINKING_CLOSE.search(unified_buffer)
                            if close_match:
                                # Send thinking content
                                thinking_text = unified_buffer[:close_match.start()]
                                if thinking_text:
                                    yield ModelResponse(content=thinking_text)

                                # Send closing tag
                                yield ModelResponse(content="\n</thinking>\n\n")
                                # Emit buffered preamble after first thinking block
                                if preamble_before_first_thinking:
                                    yield ModelResponse(content=preamble_before_first_thinking)
                                    preamble_before_first_thinking = ""
                                in_thinking = False

                                unified_buffer = unified_buffer[close_match.end():]
                                processed = True
                                continue

                        # No complete tags found - flush if buffer large
                        if not processed:
                            if len(unified_buffer) > flush_threshold:
                                # CRITICAL: Check for potential tag markers before flushing
                                contains_tag_start = '<' in unified_buffer[-tag_lookahead:]

                                if contains_tag_start:
                                    # Keep everything from last '<' onwards
                                    last_bracket_pos = unified_buffer.rfind('<')
                                    if last_bracket_pos > 0:
                                        flush_content = unified_buffer[:last_bracket_pos]
                                        if flush_content:
                                            yield ModelResponse(content=self._sanitize_stream_text(flush_content, use_thinking))
                                            unified_buffer = unified_buffer[last_bracket_pos:]
                                else:
                                    # No tag markers - flush most content, keep last tag_lookahead chars
                                    flush_content = unified_buffer[:-tag_lookahead]
                                    if flush_content:
                                        yield ModelResponse(content=self._sanitize_stream_text(flush_content, use_thinking))
                                        unified_buffer = unified_buffer[-tag_lookahead:]
                            break

                # Stream ended - process remaining buffer through tag detection
                # CRITICAL: Never send raw GLM tags - always convert them
                if unified_buffer:
                    glm_logger.info(f"[GLM Stream] Sync: Stream ended with {len(unified_buffer)} chars in buffer - processing tags")

                    # Process buffer through same tag detection logic used during streaming
                    while unified_buffer:
                        processed_at_end_sync = False

                        # 1. Check for thinking opening tag
                        if use_thinking and not in_thinking:
                            open_match = GLM_THINKING_OPEN.search(unified_buffer)
                            if open_match:
                                glm_logger.info(f"[GLM Stream] Sync: Stream-end: Opening tag detected (matched: '{open_match.group(0)}')")
                                # Send content before thinking tag
                                before_tag = unified_buffer[:open_match.start()]
                                if before_tag:
                                    glm_logger.debug(f"[GLM Stream] Sync: Stream-end: Sending {len(before_tag)} chars before opening tag")
                                    yield ModelResponse(content=before_tag)

                                # Send opening tag atomically (converted)
                                yield ModelResponse(content="<thinking>\n")
                                in_thinking = True
                                glm_logger.info("[GLM Stream] Sync: ✅ Stream-end: Entered thinking block")

                                # Continue with content after tag
                                unified_buffer = unified_buffer[open_match.end():]
                                processed_at_end_sync = True
                                continue

                        # 2. Check for thinking closing tag
                        if use_thinking and in_thinking:
                            close_match = GLM_THINKING_CLOSE.search(unified_buffer)
                            if close_match:
                                glm_logger.info(f"[GLM Stream] Sync: Stream-end: Closing tag detected (matched: '{close_match.group(0)}')")
                                # Send thinking content before closing tag
                                thinking_content = unified_buffer[:close_match.start()]
                                if thinking_content:
                                    glm_logger.debug(f"[GLM Stream] Sync: Stream-end: Sending {len(thinking_content)} chars of thinking content")
                                    yield ModelResponse(content=thinking_content)

                                # Send closing tag atomically (converted)
                                yield ModelResponse(content="\n</thinking>\n\n")
                                in_thinking = False
                                glm_logger.info("[GLM Stream] Sync: ✅ Stream-end: Exited thinking block")

                                # Continue with content after tag
                                unified_buffer = unified_buffer[close_match.end():]
                                processed_at_end_sync = True
                                continue

                        # 3. No more tags found - send remaining content
                        if not processed_at_end_sync:
                            # Check for incomplete tag fragments that should be discarded
                            stripped = unified_buffer.strip()
                            is_incomplete = (
                                (stripped.startswith('<') and not stripped.endswith('>') and len(stripped) < 30) or
                                (stripped.endswith('<') or stripped.endswith('</'))
                            )

                            if is_incomplete and len(stripped) < 30:
                                glm_logger.warning(f"[GLM Stream] Sync: ⚠️ Stream-end: Discarding incomplete tag fragment: {repr(stripped[:50])}")
                            else:
                                glm_logger.info(f"[GLM Stream] Sync: Stream-end: Sending final {len(unified_buffer)} chars")
                                yield ModelResponse(content=self._sanitize_stream_text(unified_buffer, use_thinking))

                            break  # Done processing

                break  # Success

            except Exception as e:
                attempt += 1
                should_retry = (not yielded_any) and attempt <= self.max_retries and self._is_retryable_error(e)
                if not should_retry:
                    glm_logger.error(f"Error in GLM4.5 stream: {str(e)}")
                    raise
                delay_seconds = self.initial_retry_delay * (2 ** (attempt - 1))
                glm_logger.warning(
                    f"Stream attempt {attempt} failed before first chunk: {e}. "
                    f"Retrying in {delay_seconds:.2f}s ({attempt}/{self.max_retries})"
                )
                time.sleep(delay_seconds)
            finally:
                self._use_thinking_for_next_request = None
                # Restore original max_tokens after streaming
                self.max_tokens = original_max_tokens

    def _extract_and_wrap_thinking_from_text(self, text: str) -> Optional[str]:
        """Extract GLM thinking markers and wrap them in <thinking> tags.
        Returns the transformed text if markers found, else None."""
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
        """Remove any thinking content from text. Returns new text or None if unchanged.
        
        This method aggressively removes ALL variations of thinking tags:
        - Complete tag pairs with content
        - Orphaned opening tags
        - Orphaned closing tags
        - Abbreviated forms (think/thinking)
        """
        try:
            import re
            original = text
            
            # 1. Remove complete GLM internal markers with content
            text = re.sub(r"<\|thinking\|>[\s\S]*?<\|endofthinking\|>", "", text)
            
            # 2. Remove complete XML-like thinking tags with content (both full and abbreviated)
            text = re.sub(r"<thinking>[\s\S]*?</thinking>", "", text)
            text = re.sub(r"<think>[\s\S]*?</think>", "", text)
            
            # 3. Remove orphaned opening tags (no closing tag)
            text = re.sub(r"<\|thinking\|>", "", text)
            text = re.sub(r"<thinking>", "", text)
            text = re.sub(r"<think>", "", text)
            
            # 4. Remove orphaned closing tags (no opening tag) - CRITICAL for title generation
            text = re.sub(r"<\|endofthinking\|>", "", text)
            text = re.sub(r"</thinking>", "", text)
            text = re.sub(r"</think>", "", text)
            
            # 5. Remove any remaining malformed tag fragments
            # This catches patterns like "<think", "</thin", etc.
            text = re.sub(r"</?think(?:ing)?\s*>?", "", text)
            
            new_text = text.strip()
            return new_text if new_text != original else None
        except Exception:
            return None

    def set_mode(self, mode: GLM45Mode):
        """
        Dynamically change the operation mode
        
        Args:
            mode: New operation mode
        """
        self.mode = mode
        glm_logger.info(f"Changed GLM4.5 mode to {mode.value}")

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get provider metrics for monitoring
        
        Returns:
            Dictionary of metrics
        """
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
        """Reset usage metrics"""
        self.thinking_tokens_used = 0
        self.total_thinking_time = 0.0
