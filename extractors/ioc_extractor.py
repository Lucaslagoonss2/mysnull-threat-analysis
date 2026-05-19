"""Blue Team IOC extractor with Rich-powered cyberpunk terminal UX.

This script keeps the extraction workflow practical for SOC analysts while adding:
- Rich-based terminal UI (animated startup, spinner, panel output)
- argparse command-line interface with --help
- JSON and TXT export support
- Logging + robust error handling
"""

from __future__ import annotations

import argparse
import json
import locale
import logging
import os
import random
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from ipaddress import ip_address
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set
from urllib.parse import urlparse

try:
    from extractors.rich_render import (
        render_error_panel as ui_render_error_panel,
        render_export_panel as ui_render_export_panel,
        render_normalization_notes as ui_render_normalization_notes,
        render_results as ui_render_results,
        render_success as ui_render_success,
    )
except ModuleNotFoundError:
    from rich_render import (
        render_error_panel as ui_render_error_panel,
        render_export_panel as ui_render_export_panel,
        render_normalization_notes as ui_render_normalization_notes,
        render_results as ui_render_results,
        render_success as ui_render_success,
    )

RICH_AVAILABLE = True
try:
    from rich import box
    from rich.align import Align
    from rich.console import Console, Group
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.theme import Theme
except ImportError:
    RICH_AVAILABLE = False
    # Criamos um fallback simples para evitar quebras de atributo durante o parse do script
    class FakeBox:
        DOUBLE_EDGE = None
        ROUNDED = None
        SIMPLE = None
        SIMPLE_HEAD = None
    box = FakeBox()
    Align = Console = Group = Live = Panel = Table = Text = Theme = None

# --------------------------- UI styling configuration ---------------------------

if RICH_AVAILABLE:
    CYBERPUNK_THEME = Theme(
        {
            "primary": "bold #7dd3fc",
            "accent": "bold #38bdf8",
            "info": "#bfdbfe",
            "muted": "#60a5fa",
            "success": "bold #22d3ee",
            "warning": "bold #f59e0b",
            "error": "bold #fb7185",
            "ioc.ip": "#7dd3fc",
            "ioc.domain": "#a5f3fc",
            "ioc.url": "#bae6fd",
        }
    )
    console = Console(theme=CYBERPUNK_THEME)
else:
    CYBERPUNK_THEME = None
    console = None


def detect_terminal_profile() -> Dict[str, object]:
    """Detect basic terminal capabilities for safe cross-platform rendering."""
    preferred_encoding = (locale.getpreferredencoding(False) or "").lower()
    stdout_encoding = (getattr(sys.stdout, "encoding", None) or "").lower()
    encoding = stdout_encoding or preferred_encoding
    supports_unicode = any(
        token in encoding for token in ("utf-8", "utf8", "cp65001", "utf-16", "utf16")
    )

    # Windows Terminal typically supports Unicode even when legacy code pages are present.
    if not supports_unicode and os.name == "nt" and os.environ.get("WT_SESSION"):
        supports_unicode = True

    is_tty = bool(getattr(sys.stdout, "isatty", lambda: False)())
    return {
        "encoding": encoding or "unknown",
        "supports_unicode": supports_unicode,
        "is_tty": is_tty,
    }


TERMINAL_PROFILE = detect_terminal_profile()

GLITCH_CHARS = "▓▒░#@%&*"

# Text-only terminal art (original, anime-inspired aesthetic).
REI_INSPIRED_ART = r"""
          ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⣀⣀⣀⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣠⣴⣶⣿⠿⠛⠛⠛⠻⠿⣿⣿⣿⣿⣿⣶⣤⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣴⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⢀⣿⣿⣿⣿⣿⣷⣻⠶⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠄⠂⠀⢀⣠⣾⣿⣿⣿⣿⣿⣿⣿⡄⠀⠀⠀⢀⣤⣾⣿⣿⣿⣿⣿⣿⡿⣽⣻⣳⢎⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠄⢡⠂⠄⣢⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⣶⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣟⡷⣯⡞⣝⢆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠐⠀⠁⡐⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣳⣟⡾⣹⢎⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠂⣼⣿⣿⣿⣿⡿⠿⠛⠋⠉⠀⠀⠀⠀⠀⠀⠀⠀⠉⠉⠛⠻⠿⣿⣿⣿⣿⣿⡿⣾⣝⣧⢻⡜⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢂⠐⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠂⢸⣿⡿⠟⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⠻⠿⣿⣳⢯⣞⡳⣎⠅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⢈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠄⠁⠚⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠛⢯⡞⣵⣋⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠱⣍⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⡞⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡄⢀⣾⡇⠀⣾⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣴⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⠁⣾⣿⡇⢰⣿⣿⠀⠀⣆⠀⠀⠀⠀⢰⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀⡀⠀⠀⣼⡏⢰⣿⣿⠇⣾⣿⣿⡆⠀⣿⠀⠀⠀⠀⢸⣿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⡇⠀⠀⠀⠀⠀⠀⠀⠀⠰⠃⠀⠒⠛⠃⠚⠿⣿⢰⣿⣿⣿⡇⣤⣿⣤⣶⣦⣀⢼⣿⣧⠀⢰⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⢠⣶⢰⣿⣿⣿⣧⡹⢓⣾⣾⣿⣿⣿⣧⣿⣿⣿⣿⣋⣁⣀⣀⣀⣁⠘⠃⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣾⡟⢋⠁⡀⠀⠉⠙⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠱⣚⣭⡿⢿⣿⣷⣦⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡄⢠⣆⠀⠀⠀⠀⣿⣏⡀⣾⠀⠀⠀⠀⣰⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡏⣁⠀⢠⠀⠀⠉⠻⢿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⢇⣾⣿⣷⠀⠀⠀⣿⣿⣿⣞⡓⠥⠬⣒⣷⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢿⠀⠀⠀⠀⠀⣦⠈⢳⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣾⣿⣿⣿⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣮⡢⢄⡀⠤⠾⢧⣦⣼⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⡇⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢟⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣶⣶⣶⣿⣿⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⢁⣿⣿⠇⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣏⢾⡅⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠆⣼⣿⣿⣦⣾⠀⠀⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣾⣷⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠀⠀⠀⠀⠀⢀⠰⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⣻⢿⣯⡿⣟⠇⠀⡜⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠇⠀⠀⠀⠀⠀⠌⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⢧⡟⡿⣾⡽⢏⣿⣾⣿⡌⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣛⣻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠐⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⢀⡰⣣⢻⡜⣯⢳⡝⣼⣿⣿⣿⣿⣆⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⢂⠐⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢠⠎⡵⢣⢧⡹⣜⢣⣿⣿⣿⣿⣿⣿⣿⣷⡌⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠋⠀⠀⠀⠀⠀⠀⠀⢀⠂⠔⡀⢂⠐⡀⢂⠠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠡⢚⠴⣉⠦⡑⢎⢣⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⣙⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⡩⠂⠀⠀⠀⠀⠀⣀⡔⢦⠃⢈⠐⡀⢂⠐⠠⠀⠄⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠁⠎⡰⢡⠙⡌⣸⣿⣿⣿⣿⣿⣿⣿⣿⠿⠿⠟⠒⠌⠻⢿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠛⠉⠀⠈⠀⠀⠀⠀⠀⣀⠶⡱⢎⢧⢋⠀⡐⢀⠂⠌⢀⠂⢀⠂⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠢⠑⡨⣟⠿⠟⠟⠋⠋⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠛⠛⠟⠛⠋⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢴⡩⢞⡱⢫⠜⡪⢅⠀⠂⠄⠂⠠⠀⠂⢀⠐⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢢⡙⢦⡙⡔⢣⠈⢀⠂⠈⡀⠐⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢤⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠂⠴⢉⠆⡁⠀⡀⠁⢀⠐⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠐⠡⠀⠀⠐⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠂⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
"""

BANNER_LINES = ["MYSNULL IOC CONSOLE"]
BANNER_SUBTITLE = "Threat Hunting & IOC Extraction"

# ----------------------------- IOC regex signatures -----------------------------

IP_PATTERN = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d{1,2})\.){3}(?:25[0-5]|2[0-4]\d|1?\d{1,2})\b"
)
DOMAIN_PATTERN = re.compile(r"\b(?:[a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,63}\b")
URL_PATTERN = re.compile(r"\bhttps?://[^\s\"'<>]+")
OBFUSCATED_URL_PATTERN = re.compile(r"\bhxxps?://", re.IGNORECASE)


@dataclass
class IOCResults:
    """Container for extracted IOC sets."""

    ips: Set[str]
    domains: Set[str]
    urls: Set[str]

    def to_sorted_dict(self) -> Dict[str, List[str]]:
        """Convert sets to sorted lists for stable output/export."""
        return {
            "ips": sorted(self.ips),
            "domains": sorted(self.domains),
            "urls": sorted(self.urls),
        }

    def to_dict(self) -> Dict[str, List[str]]:
        """Backward-compatible alias."""
        return self.to_sorted_dict()

    def __getitem__(self, key: str) -> List[str]:
        """Support legacy dict-style indexing, e.g. results['ips']."""
        return self.to_sorted_dict()[key]

    def get(self, key: str, default=None):
        """Support legacy dict-like .get access."""
        return self.to_sorted_dict().get(key, default)


@dataclass
class IOCNormalizationStats:
    """Extraction normalization metadata for lightweight analyst notes."""

    obfuscated_schemes_normalized: int = 0
    duplicates_removed: int = 0
    private_ips_filtered: int = 0


def build_parser() -> argparse.ArgumentParser:
    """Create CLI parser (includes --help automatically)."""
    parser = argparse.ArgumentParser(
        description=(
            "Extract IPs, domains, and URLs from log text with a lightweight IOC console."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to the log/text file you want to scan.",
    )
    parser.add_argument(
        "-f",
        "--formats",
        nargs="+",
        choices=("json", "txt"),
        default=["txt"],
        help="One or more export formats.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=".",
        help="Directory where output files are written.",
    )
    parser.add_argument(
        "-b",
        "--basename",
        default="ioc_results",
        help="Base file name used for exports.",
    )
    parser.add_argument(
        "--log-file",
        default="ioc_extractor.log",
        help="Path for the run log file.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable additional logging in terminal output.",
    )
    parser.add_argument(
        "--no-animation",
        action="store_true",
        help="Disable startup animations/delays for fast runs.",
    )
    parser.add_argument(
        "--exclude-private-ips",
        action="store_true",
        help="Filter private/reserved IPv4 values from the final IOC output.",
    )
    return parser


def setup_logging(log_file: Path, verbose: bool) -> logging.Logger:
    """Configure file + optional console logging."""
    logger = logging.getLogger("ioc_extractor")
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    log_file.parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if verbose:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def glitch_text(text: str, intensity: float = 0.08) -> str:
    """Apply a light glitch effect by replacing random characters."""
    glitched_chars = []
    for char in text:
        if char not in {" ", "\n"} and random.random() < intensity:
            glitched_chars.append(random.choice(GLITCH_CHARS))
        else:
            glitched_chars.append(char)
    return "".join(glitched_chars)


def build_banner_panel(glitch_intensity: float) -> Panel:
    """Compose the top terminal banner panel."""
    banner = "\n".join(glitch_text(line, glitch_intensity) for line in BANNER_LINES)

    content = Group(
        Align.center(Text(banner, style="primary")),
        Align.center(Text(glitch_text(BANNER_SUBTITLE, glitch_intensity * 0.25), style="muted")),
    )
    return Panel(
        content,
        border_style="accent",
        box=box.DOUBLE_EDGE,
        title="[primary]MYSNULL IOC CONSOLE[/primary]",
        subtitle=f"[muted]{BANNER_SUBTITLE}[/muted]",
        padding=(1, 2),
    )


def show_startup_banner(disable_animation: bool) -> None:
    """Display animated startup banner."""
    if disable_animation:
        console.print(build_banner_panel(0.0))
        return

    intensities = [0.30, 0.24, 0.18, 0.12, 0.08, 0.04, 0.0]
    with Live(
        build_banner_panel(intensities[0]),
        console=console,
        refresh_per_second=16,
        transient=False,
    ) as live:
        for level in intensities[1:]:
            time.sleep(0.12)
            live.update(build_banner_panel(level))


def run_boot_sequence(disable_animation: bool) -> None:
    """Show spinner + animated status messages."""
    status_steps = [
        "Initializing terminal overlays...",
        "Loading IOC regex signatures...",
        "Calibrating threat hunting workspace...",
        "Preparing analyst workspace...",
    ]

    if disable_animation:
        for step in status_steps:
            console.print(f"[info]• {step}")
        return

    with console.status(
        "[accent]Boot sequence started...[/accent]",
        spinner="dots",
        spinner_style="accent",
    ) as status:
        for step in status_steps:
            status.update(f"[accent]{step}[/accent]")
            time.sleep(0.45)


def read_input_file(path: Path) -> str:
    """Read target log file safely."""
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    if not path.is_file():
        raise IsADirectoryError(f"Input path is not a file: {path}")
    return path.read_text(encoding="utf-8", errors="ignore")


def normalize_url_candidate(url: str) -> str:
    """Trim trailing punctuation commonly attached to URLs in logs."""
    return url.strip().rstrip(".,);]")

def normalize_domain_candidate(domain: str) -> str:
    """Normalize case and trailing dots for domains/hostnames."""
    return domain.strip().rstrip(".").lower()
def deobfuscate_hxxp_schemes(text: str) -> tuple[str, int]:
    """Normalize hxxp/hxxps obfuscated schemes to http/https."""
    replacements = 0

    def _replace(match: re.Match[str]) -> str:
        nonlocal replacements
        replacements += 1
        token = match.group(0).lower()
        return "https://" if token.startswith("hxxps") else "http://"

    return OBFUSCATED_URL_PATTERN.sub(_replace, text), replacements

def is_public_ipv4(value: str) -> bool:
    """Return True only for globally routable IPv4 addresses."""
    try:
        return ip_address(value).is_global
    except ValueError:
        return False

def dedupe_count(values: Sequence[str]) -> int:
    """Return the count of duplicates removed by set-based normalization."""
    return max(0, len(values) - len(set(values)))

def build_normalization_notes(stats: IOCNormalizationStats) -> List[str]:
    """Build concise analyst-oriented normalization notes."""
    notes: List[str] = []
    if stats.obfuscated_schemes_normalized:
        notes.append(
            f"Normalized {stats.obfuscated_schemes_normalized} obfuscated URL scheme(s) (hxxp/hxxps)."
        )
    if stats.duplicates_removed:
        notes.append(f"Removed {stats.duplicates_removed} duplicate IOC value(s).")
    if stats.private_ips_filtered:
        notes.append(f"Filtered {stats.private_ips_filtered} private/reserved IP address(es).")
    return notes

def extract_urls(text: str) -> Set[str]:
    """Extract and normalize URL candidates from text."""
    return {normalize_url_candidate(url) for url in URL_PATTERN.findall(text)}

def extract_domains(text: str) -> Set[str]:
    """Extract and normalize domain candidates from text."""
    domains: Set[str] = set()
    for domain in DOMAIN_PATTERN.findall(text):
        normalized = normalize_domain_candidate(domain)
        if normalized:
            domains.add(normalized)
    return domains

def extract_domains_from_urls(urls: Iterable[str]) -> Set[str]:
    """Collect hostnames from parsed URLs."""
    domains: Set[str] = set()
    for url in urls:
        parsed = urlparse(url)
        if parsed.hostname:
            domains.add(normalize_domain_candidate(parsed.hostname))
    return {domain for domain in domains if domain}

def is_ip_literal(value: str) -> bool:
    """Return True if value is an IPv4 literal."""
    return IP_PATTERN.fullmatch(value) is not None
def extract_iocs_with_stats(
    text: str, exclude_private_ips: bool = False
) -> tuple[IOCResults, IOCNormalizationStats]:
    """Extract IOCs and return normalization metadata."""
    normalized_text, normalized_scheme_count = deobfuscate_hxxp_schemes(text)

    raw_ips = IP_PATTERN.findall(normalized_text)
    raw_urls = [normalize_url_candidate(url) for url in URL_PATTERN.findall(normalized_text)]
    raw_domains = [
        normalize_domain_candidate(domain) for domain in DOMAIN_PATTERN.findall(normalized_text)
    ]
    raw_domain_hosts = [
        normalize_domain_candidate(urlparse(url).hostname or "")
        for url in raw_urls
        if urlparse(url).hostname
    ]

    ips = set(raw_ips)
    if exclude_private_ips:
        public_ips = {ip for ip in ips if is_public_ipv4(ip)}
        private_ips_filtered = len(ips) - len(public_ips)
        ips = public_ips
    else:
        private_ips_filtered = 0

    urls = {url for url in raw_urls if url}
    combined_domains = [domain for domain in [*raw_domains, *raw_domain_hosts] if domain]
    domains = {domain for domain in combined_domains if not is_ip_literal(domain)}

    stats = IOCNormalizationStats(
        obfuscated_schemes_normalized=normalized_scheme_count,
        duplicates_removed=(
            dedupe_count(raw_ips)
            + dedupe_count(raw_urls)
            + dedupe_count([domain for domain in combined_domains if not is_ip_literal(domain)])
        ),
        private_ips_filtered=private_ips_filtered,
    )
    return IOCResults(ips=ips, domains=domains, urls=urls), stats


def extract_iocs(text: str, exclude_private_ips: bool = False) -> IOCResults:
    """Extract IOC artifacts from text using regex patterns."""
    results, _ = extract_iocs_with_stats(text, exclude_private_ips=exclude_private_ips)
    return results



def export_json(results: IOCResults, path: Path, source_file: Path) -> None:
    """Write IOC data to JSON."""
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_file": str(source_file),
        "counts": {
            "ips": len(results.ips),
            "domains": len(results.domains),
            "urls": len(results.urls),
        },
        "iocs": results.to_sorted_dict(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def export_txt(results: IOCResults, path: Path, source_file: Path) -> None:
    """Write IOC data to text report."""
    lines = [
        "=== BLUE TEAM IOC REPORT ===",
        f"Generated UTC: {datetime.now(timezone.utc).isoformat()}",
        f"Source File: {source_file}",
        "",
        f"IPs Found: {len(results.ips)}",
        f"Domains Found: {len(results.domains)}",
        f"URLs Found: {len(results.urls)}",
        "",
        "=== IP ADDRESSES ===",
        *sorted(results.ips),
        "",
        "=== DOMAINS ===",
        *sorted(results.domains),
        "",
        "=== URLS ===",
        *sorted(results.urls),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def export_results(
    results: IOCResults,
    formats: Sequence[str],
    output_dir: Path,
    basename: str,
    source_file: Path,
) -> List[Path]:
    """Export IOC results in requested format(s)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    written_files: List[Path] = []

    # dict.fromkeys preserves order while removing duplicates.
    for fmt in dict.fromkeys(formats):
        output_path = output_dir / f"{basename}.{fmt}"
        if fmt == "json":
            export_json(results, output_path, source_file)
        elif fmt == "txt":
            export_txt(results, output_path, source_file)
        else:
            raise ValueError(f"Unsupported export format: {fmt}")
        written_files.append(output_path)

    return written_files

def should_use_rich_ui() -> bool:
    """Decide whether full Rich UI should be used."""
    return (
        RICH_AVAILABLE
        and console is not None
        and bool(TERMINAL_PROFILE.get("supports_unicode"))
        and bool(TERMINAL_PROFILE.get("is_tty"))
    )


def show_plain_startup_banner() -> None:
    """Show a safe plain-text startup banner."""
    sys.stdout.write(f"\n{BANNER_LINES[0]}\n{BANNER_SUBTITLE}\n\n")


def render_plain_error(title: str, message: str) -> None:
    """Render plain-text error output."""
    sys.stderr.write(f"{title}: {message}\n")


def render_plain_results(results: IOCResults) -> None:
    """Render extraction results without Rich dependencies."""
    print("IOC RESULTS")
    print(f"IPs ({len(results.ips)}): {sorted(results.ips)}")
    print(f"Domains ({len(results.domains)}): {sorted(results.domains)}")
    print(f"URLs ({len(results.urls)}): {sorted(results.urls)}")


def render_plain_normalization_notes(notes: Sequence[str]) -> None:
    """Render normalization notes in plain mode."""
    if not notes:
        return
    print("Normalization Notes:")
    for note in notes:
        print(f"- {note}")


def render_plain_export_panel(exported_files: Sequence[Path], log_file: Path) -> None:
    """Render export artifact paths in plain mode."""
    print("Artifacts:")
    for path in exported_files:
        print(f"- {path}")
    print(f"- log: {log_file}")



def run_extractor(args: argparse.Namespace) -> int:
    """Main app workflow. Returns process exit code."""
    rich_ui = should_use_rich_ui()
    if not rich_ui and args.verbose:
        sys.stdout.write(
            f"Using plain terminal mode (encoding={TERMINAL_PROFILE.get('encoding')}).\n"
        )

    log_file = Path(args.log_file).expanduser()
    logger = setup_logging(log_file=log_file, verbose=args.verbose)
    logger.info("IOC extractor started")

    input_path = Path(args.input).expanduser()
    output_dir = Path(args.output_dir).expanduser()
    if rich_ui:
        show_startup_banner(args.no_animation)
        run_boot_sequence(args.no_animation)
    else:
        show_plain_startup_banner()

    try:
        if rich_ui:
            with console.status(
                "[accent]Reading source file and extracting IOCs...[/accent]",
                spinner="dots",
                spinner_style="accent",
            ):
                content = read_input_file(input_path)
                if not args.no_animation:
                    time.sleep(0.25)
                results, normalization_stats = extract_iocs_with_stats(
                    content, exclude_private_ips=args.exclude_private_ips
                )
        else:
            content = read_input_file(input_path)
            results, normalization_stats = extract_iocs_with_stats(
                content, exclude_private_ips=args.exclude_private_ips
            )
    except (FileNotFoundError, IsADirectoryError) as exc:
        logger.error("Input error: %s", exc)
        if rich_ui:
            ui_render_error_panel(
                console=console,
                Panel=Panel,
                title="[error]Input Error[/error]",
                message=str(exc),
            )
        else:
            render_plain_error("Input Error", str(exc))
        return 1
    except OSError as exc:
        logger.exception("OS error while reading input file")
        if rich_ui:
            ui_render_error_panel(
                console=console,
                Panel=Panel,
                title="[error]File Read Error[/error]",
                message=f"Unable to read input file: {exc}",
            )
        else:
            render_plain_error("File Read Error", f"Unable to read input file: {exc}")
        return 1
    except Exception:
        logger.exception("Unexpected error during IOC extraction")
        if rich_ui:
            ui_render_error_panel(
                console=console,
                Panel=Panel,
                title="[error]Unexpected Error[/error]",
                message="Unexpected extraction failure. Review log file for details.",
            )
        else:
            render_plain_error(
                "Unexpected Error",
                "Unexpected extraction failure. Review log file for details.",
            )
        return 1
    normalization_notes = build_normalization_notes(normalization_stats)

    logger.info(
        "Extraction complete | ips=%d domains=%d urls=%d",
        len(results.ips),
        len(results.domains),
        len(results.urls),
    )
    if normalization_notes:
        logger.info("Normalization | %s", " | ".join(normalization_notes))
    try:
        if rich_ui:
            ui_render_results(
                console=console,
                box=box,
                Table=Table,
                Panel=Panel,
                results=results,
            )
            ui_render_normalization_notes(
                console=console,
                box=box,
                Panel=Panel,
                notes=normalization_notes,
            )
        else:
            render_plain_results(results)
            render_plain_normalization_notes(normalization_notes)
    except Exception:
        logger.exception("Failed to render results panel")
        if rich_ui:
            console.print(
                "[warning]Extraction succeeded, but result rendering failed. Check logs.[/warning]"
            )
        else:
            render_plain_error(
                "Warning", "Extraction succeeded, but result rendering failed. Check logs."
            )

    try:
        exported_files = export_results(
            results=results,
            formats=args.formats,
            output_dir=output_dir,
            basename=args.basename,
            source_file=input_path,
        )
    except OSError:
        logger.exception("Failed to write export files")
        if rich_ui:
            ui_render_error_panel(
                console=console,
                Panel=Panel,
                title="[error]Export Error[/error]",
                message="Export failed due to a file system error. Check permissions/path.",
            )
        else:
            render_plain_error(
                "Export Error",
                "Export failed due to a file system error. Check permissions/path.",
            )
        return 1
    except Exception:
        logger.exception("Unexpected error while exporting results")
        if rich_ui:
            ui_render_error_panel(
                console=console,
                Panel=Panel,
                title="[error]Unexpected Error[/error]",
                message="Unexpected export failure. Review log file for details.",
            )
        else:
            render_plain_error(
                "Unexpected Error",
                "Unexpected export failure. Review log file for details.",
            )
        return 1

    logger.info("Export complete | files=%s", ", ".join(str(path) for path in exported_files))
    try:
        if rich_ui:
            ui_render_export_panel(
                console=console,
                box=box,
                Panel=Panel,
                exported_files=exported_files,
                log_file=log_file,
            )
        else:
            render_plain_export_panel(exported_files=exported_files, log_file=log_file)
    except Exception:
        logger.exception("Failed to render export artifacts panel")
        if rich_ui:
            console.print(
                "[warning]Export succeeded, but artifact panel rendering failed. Check logs.[/warning]"
            )
        else:
            render_plain_error(
                "Warning", "Export succeeded, but artifact rendering failed. Check logs."
            )

    if rich_ui:
        ui_render_success(console=console, message="IOC extraction complete.")
    else:
        print("IOC extraction complete.")
    return 0

def main() -> int:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args()
    return run_extractor(args)


if __name__ == "__main__":
    sys.exit(main())