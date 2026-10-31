"""Unit tests for the streaming-router fallback + provider stream contract.

The end-to-end SSE path is exercised by the smoke run in CI/curl; here we
just lock in the contract every provider must honour: ``stream_text`` yields
StreamDelta events for token batches and terminates with one LLMResponse.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.llm.router import Router
from app.llm.types import LLMRequest, LLMResponse, StreamDelta


class _StubStreamProvider:
    def __init__(
        self, name: str, deltas: list[str], fail: bool = False, fail_models: set[str] | None = None
    ) -> None:
        self.name = name
        self._deltas = deltas
        self._fail = fail
        self._fail_models = fail_models or set()
        self.calls = 0

    async def generate(self, request):  # not used here
        raise NotImplementedError

    async def stream_text(self, request: LLMRequest):
        self.calls += 1
        if self._fail or request.model in self._fail_models:
            raise RuntimeError(f"{self.name} stream init failed")
        for d in self._deltas:
            yield StreamDelta(text=d)
        yield LLMResponse(
            text="".join(self._deltas),
            provider=self.name,
            model=request.model,
            prompt_tokens=10,
            completion_tokens=len("".join(self._deltas).split()),
            total_tokens=10 + len("".join(self._deltas).split()),
            latency_ms=1,
            estimated_cost_eur=Decimal("0.0001"),
        )


# Routing table: cover_letter → default anthropic/sonnet, fallback anthropic/haiku.


@pytest.mark.asyncio
async def test_route_stream_yields_deltas_then_final_from_default() -> None:
    anthropic = _StubStreamProvider("anthropic", ["Hello, ", "world!"])
    openai = _StubStreamProvider("openai", ["unused"])
    router = Router({"openai": openai, "anthropic": anthropic})

    events: list = []
    async for ev in router.route_stream(
        "cover_letter",
        LLMRequest(system="s", messages=[], model="placeholder"),
    ):
        events.append(ev)

    deltas = [e for e in events if isinstance(e, StreamDelta)]
    finals = [e for e in events if isinstance(e, LLMResponse)]
    assert [d.text for d in deltas] == ["Hello, ", "world!"]
    assert len(finals) == 1
    assert finals[0].provider == "anthropic"
    assert anthropic.calls == 1
    assert openai.calls == 0


@pytest.mark.asyncio
async def test_route_stream_falls_back_when_default_fails_before_emitting() -> None:
    anthropic = _StubStreamProvider(
        "anthropic", ["Fallback ", "wins."], fail_models={"claude-sonnet-4-6"}
    )
    openai = _StubStreamProvider("openai", ["unused"])
    router = Router({"openai": openai, "anthropic": anthropic})

    deltas: list[str] = []
    final_model: str | None = None
    async for ev in router.route_stream(
        "cover_letter",
        LLMRequest(system="s", messages=[], model="placeholder"),
    ):
        if isinstance(ev, StreamDelta):
            deltas.append(ev.text)
        elif isinstance(ev, LLMResponse):
            final_model = ev.model

    assert deltas == ["Fallback ", "wins."]
    assert final_model == "claude-haiku-4-5"
    assert anthropic.calls == 2   # default model, then fallback model
    assert openai.calls == 0
