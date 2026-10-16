import logging
import contextvars
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone

from tenacity import RetryCallState, retry, retry_if_exception, stop_after_attempt, wait_exponential

from .request_utils import HEADERS, LLMRateLimitExceeded, RateLimit, async_request_template
from .tool_config import LLMServerInfo


def llm_should_retry(exception: BaseException) -> bool:
    if isinstance(exception, (KeyboardInterrupt, NotImplementedError, LLMRateLimitExceeded)):
        return False
    return True


def _log_retry(retry_state: RetryCallState):
    """Log the concrete error before tenacity sleeps and makes the next attempt."""
    error = retry_state.outcome.exception() if retry_state.outcome else None
    logging.warning(
        "LLM request failed; retrying attempt=%d/%d error_type=%s error=%s",
        retry_state.attempt_number,
        3,
        type(error).__name__ if error else "unknown",
        error,
    )


class AsyncLLMClient(ABC):
    """Shared LLM transport with per-evaluation primary availability and fallback."""

    _fallback_llm: LLMServerInfo | None = None
    _evaluation_state = contextvars.ContextVar("llm_evaluation_state", default=None)

    def __init__(self, llm: LLMServerInfo, sampling_params: dict | None = None):
        self.llm = llm
        self.timeout = 600
        self.sampling_params = sampling_params or {}

    @classmethod
    def begin_evaluation(cls, config):
        """Refresh primary availability once at the start of one article evaluation."""
        AsyncLLMClient._fallback_llm = getattr(config, "fallback_llm_info", None)
        AsyncLLMClient._evaluation_state.set({
            "primary_servers": {
                "external_llm": config.llm_server_info,
                "agent": config.agent_info,
            },
            "available": {"external_llm": True, "agent": True},
            "fallback": getattr(config, "fallback_llm_info", None),
            "slot": AsyncLLMClient._quota_slot(),
        })

    @classmethod
    def configure_fallback(cls, fallback_llm: LLMServerInfo | None):
        """Backward-compatible fallback configuration; does not reset primary state."""
        AsyncLLMClient._fallback_llm = fallback_llm

    @staticmethod
    def _beijing_now() -> datetime:
        return datetime.now(timezone(timedelta(hours=8)))

    @classmethod
    def _quota_slot(cls) -> tuple[int, int]:
        now = cls._beijing_now()
        refresh_hour = max(hour for hour in (0, 5, 10, 15, 20) if hour <= now.hour)
        return now.date().toordinal(), refresh_hour

    @classmethod
    def _provider_name(cls, server: LLMServerInfo) -> str:
        state = cls._evaluation_state.get() or {}
        for name, configured in state.get("primary_servers", {}).items():
            if server == configured:
                return name
        return "external_llm"

    @classmethod
    def _server_available(cls, server: LLMServerInfo) -> bool:
        state = cls._evaluation_state.get() or {}
        return state.get("available", {}).get(cls._provider_name(server), True)

    @classmethod
    def _mark_unavailable(cls, server: LLMServerInfo) -> bool:
        state = cls._evaluation_state.get()
        if state is None:
            return False
        name = cls._provider_name(server)
        was_available = state["available"].get(name, True)
        state["available"][name] = False
        return was_available

    @classmethod
    def _refresh_if_due(cls):
        state = cls._evaluation_state.get()
        if state is None:
            return
        current_slot = cls._quota_slot()
        if state["slot"] != current_slot:
            for name in state["available"]:
                state["available"][name] = True
            state["slot"] = current_slot

    @classmethod
    def _fallback_for(cls, server: LLMServerInfo) -> LLMServerInfo | None:
        cls._refresh_if_due()
        state = cls._evaluation_state.get() or {}
        fallback = state.get("fallback", cls._fallback_llm)
        return fallback if not cls._server_available(server) else None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1.5, min=1, max=10),
        retry=retry_if_exception(llm_should_retry),
        before_sleep=_log_retry,
    )
    async def _post_primary(self, endpoint: str, payload: dict, context: dict):
        try:
            return await self._post_server(self.llm, endpoint, payload, context)
        except LLMRateLimitExceeded:
            first_transition = self._mark_unavailable(self.llm)
            provider = self._provider_name(self.llm)
            state = AsyncLLMClient._evaluation_state.get() or {}
            fallback = state.get("fallback", AsyncLLMClient._fallback_llm)
            if first_transition:
                logging.warning("%s quota exhausted; switching to fallback LLM", provider)
            if fallback is None:
                raise
            return await self._post_server_retry(fallback, endpoint, payload, context)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1.5, min=1, max=10),
        retry=retry_if_exception(llm_should_retry),
        before_sleep=_log_retry,
    )
    async def _post_server_retry(
        self,
        server: LLMServerInfo,
        endpoint: str,
        payload: dict,
        context: dict,
    ):
        """Send a request to a selected LLM server with retries."""
        return await self._post_server(server, endpoint, payload, context)

    async def _post_server(self, server: LLMServerInfo, endpoint: str, payload: dict, context: dict):
        url = f"{server.base_url.rstrip('/')}/v1/{endpoint}"
        headers = {"Authorization": f"Bearer {server.api_key}"} | HEADERS
        request_payload = {**payload, "model": server.model}
        async with RateLimit.AGENT_SEMAPHORE:
            data = await async_request_template("post", url, headers, request_payload, timeout=self.timeout)
        if endpoint == "chat/completions":
            data = data["choices"][0]["message"]["content"]
            if "</think>" in data:
                data = data.split("</think>")[-1]
        return self._availability(data, context)

    @abstractmethod
    def _availability(self, response, context):
        raise NotImplementedError

    async def _post(self, endpoint: str, payload: dict, context: dict):
        fallback = self._fallback_for(self.llm)
        if fallback is not None:
            return await self._post_server_retry(fallback, endpoint, payload, context)
        return await self._post_primary(endpoint, payload, context)


class AsyncChat(AsyncLLMClient):
    PROMPT: str = ""

    def _organize_inputs(self, inputs: dict):
        return self.PROMPT.format(**inputs), {}

    async def call(self, messages=None, inputs=None, context=None, **kwargs):
        context = context or {}
        assert inputs or messages, "Must have messages or inputs for chat/completions"
        if messages is None:
            messages, new_context = self._organize_inputs(inputs)
            context = {**context, **new_context}
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        payload = {"model": self.llm.model, "messages": messages, **self.sampling_params, **kwargs}
        return await self._post("chat/completions", payload, context)


class AsyncRerank(AsyncLLMClient):
    def _availability(self, response, context):
        return [x["document"]["text"] for x in response["results"]]

    async def call(self, query, documents, top_n, context=None, **kwargs):
        context = context or {}
        payload = {"model": self.llm.model, "query": query, "documents": documents, "top_n": top_n, **kwargs}
        return await self._post("rerank", payload, context)
