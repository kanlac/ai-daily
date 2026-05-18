'''Base collector contracts.'''
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Protocol
from daily_brief.config import SourceConfig
from daily_brief.models import CollectedItem

@dataclass(slots=True)
class CollectorResult:
    source_id: str
    items: list[CollectedItem]
    warnings: list[str] = field(default_factory=list)
    degraded: bool = False

class Collector(Protocol):
    def collect(self, source: SourceConfig, run_date: str) -> CollectorResult:
        '''Collect read-only public items for one source.'''
