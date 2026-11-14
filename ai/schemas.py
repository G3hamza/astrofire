"""Pydantic request/response models for the AI endpoints (documented in docs/DATA_CONTRACTS.md (B) and docs/AI_LAYER.md)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Habitat = Literal["iss", "spacecraft", "exploration", "moon", "rover", "mars"]


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class AskIn(BaseModel):
    """POST /api/ask (analyst) and POST /ai/chat."""
    question: str = Field(min_length=1, max_length=2000)
    habitat: Habitat | None = None
    history: list[Turn] = Field(default_factory=list, max_length=20)


class Source(BaseModel):
    model_config = ConfigDict(extra="allow")
    n: int
    title: str | None = None
    year: str | None = None
    url: str | None = None
    chunk_id: str | None = None
    snippet: str = ""


class AskOut(BaseModel):
    """Stable analyst contract. Extra keys are allowed (entities, guardrails ...)."""
    model_config = ConfigDict(extra="allow")
    answer: str
    findings: list[str]
    interpretation: list[str]
    limits: list[str]
    followups: list[str]
    tools_used: list[str]
    mode: Literal["ai", "template"]
    model: str | None
    intent: str
    evidence: list[dict]
    sources: list[Source]
    suggested_followups: list[str]
    insufficient_evidence: bool
    request_id: str
    latency_ms: int


class SimpleAskIn(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    investigation: str | None = Field(None, max_length=40)


class ScenarioIn(BaseModel):
    environment: str = Field("iss", max_length=20)
    o2: float | None = Field(None, ge=0, le=100)
    pressure: float | None = Field(None, ge=1, le=600)
    material: str | None = Field(None, max_length=60)
    fuel_type: str | None = Field(None, max_length=30)
    gravity_g: float | None = Field(None, ge=0, le=1.5)
    flow_cm_s: float = Field(5.0, ge=0, le=200)


class CompareIn(BaseModel):
    ids: list[str] = Field(min_length=2, max_length=3)


class GapsIn(BaseModel):
    scenario: ScenarioIn | None = None
