"""
PromptStrike - Developer-first automated LLM red-team platform

Reference: cid-onepager-v1, cid-roadmap-v1 Sprint S-1
"""

__version__ = "0.1.0"
__author__ = "PromptStrike Team"
__email__ = "dev@promptstrike.com"
__license__ = "MIT"

from .core.scanner import LLMScanner
from .core.report import ReportGenerator
from .core.attacks import AttackPackLoader
from .models.scan_result import ScanResult, AttackResult

__all__ = [
    "LLMScanner",
    "ReportGenerator", 
    "AttackPackLoader",
    "ScanResult",
    "AttackResult",
]