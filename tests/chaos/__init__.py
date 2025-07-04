"""
Chaos Engineering Test Suite for PromptStrike

This module provides chaos engineering capabilities for testing the resilience
of the PromptStrike replay engine and core components under adverse conditions.

Features:
- Mutation testing for data corruption scenarios
- Malformed span injection
- Network failure simulation
- Resource exhaustion testing
- Gork (garbled data) generation
"""

from .mutation_engine import MutationEngine, MutationType
from .chaos_replay import ChaosReplayEngine
from .span_mutator import SpanMutator, MalformedSpanGenerator
from .gork_generator import GorkGenerator, GorkType
from .fault_injector import FaultInjector, FaultType

__all__ = [
    'MutationEngine',
    'MutationType', 
    'ChaosReplayEngine',
    'SpanMutator',
    'MalformedSpanGenerator',
    'GorkGenerator',
    'GorkType',
    'FaultInjector',
    'FaultType'
]