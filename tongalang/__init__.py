"""
TongaLang package.

TongaLang is a minimal interpreted educational programming language
using Tonga-derived keywords for beginner programming education.
"""

__version__ = "0.2.0"

from .runner import run_source, run_file, safe_run_source, safe_run_file
from .diagnostics import (
    Diagnostic,
    DiagnosticSeverity,
    SourceSpan,
    SuggestedFix,
    TextEdit,
    analyze_source,
    apply_fix,
)

__all__ = [
    "run_source",
    "run_file",
    "safe_run_source",
    "safe_run_file",
    "Diagnostic",
    "DiagnosticSeverity",
    "SourceSpan",
    "SuggestedFix",
    "TextEdit",
    "analyze_source",
    "apply_fix",
]
