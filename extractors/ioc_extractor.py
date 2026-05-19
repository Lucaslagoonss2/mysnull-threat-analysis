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
import logging
import random
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set
from urllib.parse import urlparse

try:
    from extractors.rich_render import (
        render_error_panel as ui_render_error_panel,
        render_export_panel as ui_render_export_panel,
        render_results as ui_render_results,
        render_success as ui_render_success,
    )
except ModuleNotFoundError:
    from rich_render import (
        render_error_panel as ui_render_error_panel,
        render_export_panel as ui_render_export_panel,
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

BANNER_LINES = [
    "██████╗ ██╗     ██╗    ██╗███████╗    ████████╗███████╗ █████╗ ███╗   ███╗",
    "██╔══██╗██║     ██║    ██║██╔════╝    ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║",
    "██████╔╝██║     ██║    ██║█████╗         ██║   █████╗  ███████║██╔████╔██║",
    "██╔══██╗██║     ██║    ██║██╔══╝         ██║   ██╔══╝  ██╔══██║██║╚██╔╝██║",
    "██████╔╝███████╗╚██████╔╝███████╗       ██║   ███████╗██║  ██║██║ ╚═╝ ██║",
    "╚═════╝ ╚══════╝ ╚═════╝ ╚══════╝       ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝",
]

# ----------------------------- IOC regex signatures -----------------------------

IP_PATTERN = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d{1,2})\.){3}(?:25[0-5]|2[0-4]\d|1?\d{1,2})\b"
)
DOMAIN_PATTERN = re.compile(r"\b(?:[a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,63}\b")
URL_PATTERN = re.compile(r"\bhttps?://[^\s\"'<>]+")


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


def build_parser() -> argparse.ArgumentParser:
    """Create CLI parser (includes --help automatically)."""
    parser = argparse.ArgumentParser(
        description=(
            "Extract IPs, domains, and URLs from log text with a cyberpunk Blue Team "
            "terminal interface."
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
    portrait = glitch_text(REI_INSPIRED_ART, glitch_intensity * 0.8)

    content = Group(
        Align.center(Text(banner, style="primary")),
        Align.center(Text(portrait, style="accent")),
        Align.center(
            Text(
                "CYBERPUNK BLUE TEAM IOC TERMINAL // PROFESSIONAL SOC UTILITY MODE",
                style="muted",
            )
        ),
    )
    return Panel(
        content,
        border_style="accent",
        box=box.DOUBLE_EDGE,
        title="[primary]SENTINEL CONSOLE[/primary]",
        subtitle="[muted]text-only art · no external images[/muted]",
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
        "Calibrating Blue Team telemetry channels...",
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


def extract_iocs(text: str) -> IOCResults:
    """Extract IOC artifacts from text using regex patterns."""
    ips = set(IP_PATTERN.findall(text))
    urls = extract_urls(text)
    domains = extract_domains(text)
    domains.update(extract_domains_from_urls(urls))
    domains = {domain for domain in domains if not is_ip_literal(domain)}

    return IOCResults(ips=ips, domains=domains, urls=urls)



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



def run_extractor(args: argparse.Namespace) -> int:
    """Main app workflow. Returns process exit code."""
    # A verificação de dependência agora joga direto para o stderr padrão antes de quebrar
    if not RICH_AVAILABLE or console is None:
        sys.stderr.write(
            "Error: Missing dependency 'rich'. Install it with 'pip install rich' and run again.\n"
        )
        return 1

    log_file = Path(args.log_file).expanduser()
    logger = setup_logging(log_file=log_file, verbose=args.verbose)
    logger.info("IOC extractor started")

    input_path = Path(args.input).expanduser()
    output_dir = Path(args.output_dir).expanduser()

    show_startup_banner(args.no_animation)
    run_boot_sequence(args.no_animation)

    try:
        with console.status(
            "[accent]Reading source file and extracting IOCs...[/accent]",
            spinner="dots",
            spinner_style="accent",
        ):
            content = read_input_file(input_path)
            if not args.no_animation:
                time.sleep(0.25)
            results = extract_iocs(content)
    except (FileNotFoundError, IsADirectoryError) as exc:
        logger.error("Input error: %s", exc)
        ui_render_error_panel(
            console=console,
            Panel=Panel,
            title="[error]Input Error[/error]",
            message=str(exc),
        )
        return 1
    except OSError as exc:
        logger.exception("OS error while reading input file")
        ui_render_error_panel(
            console=console,
            Panel=Panel,
            title="[error]File Read Error[/error]",
            message=f"Unable to read input file: {exc}",
        )
        return 1
    except Exception:
        logger.exception("Unexpected error during IOC extraction")
        ui_render_error_panel(
            console=console,
            Panel=Panel,
            title="[error]Unexpected Error[/error]",
            message="Unexpected extraction failure. Review log file for details.",
        )
        return 1

    logger.info(
        "Extraction complete | ips=%d domains=%d urls=%d",
        len(results.ips),
        len(results.domains),
        len(results.urls),
    )
    try:
        ui_render_results(
            console=console,
            box=box,
            Table=Table,
            Panel=Panel,
            results=results,
        )
    except Exception:
        logger.exception("Failed to render results panel")
        console.print(
            "[warning]Extraction succeeded, but result rendering failed. Check logs.[/warning]"
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
        ui_render_error_panel(
            console=console,
            Panel=Panel,
            title="[error]Export Error[/error]",
            message="Export failed due to a file system error. Check permissions/path.",
        )
        return 1
    except Exception:
        logger.exception("Unexpected error while exporting results")
        ui_render_error_panel(
            console=console,
            Panel=Panel,
            title="[error]Unexpected Error[/error]",
            message="Unexpected export failure. Review log file for details.",
        )
        return 1

    logger.info("Export complete | files=%s", ", ".join(str(path) for path in exported_files))
    try:
        ui_render_export_panel(
            console=console,
            box=box,
            Panel=Panel,
            exported_files=exported_files,
            log_file=log_file,
        )
    except Exception:
        logger.exception("Failed to render export artifacts panel")
        console.print(
            "[warning]Export succeeded, but artifact panel rendering failed. Check logs.[/warning]"
        )

    ui_render_success(console=console, message="IOC extraction complete.")
    return 0

def main() -> int:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args()
    return run_extractor(args)


if __name__ == "__main__":
    sys.exit(main())