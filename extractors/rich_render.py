"""Rich terminal rendering helpers for IOC extractor UI output."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, List, Sequence


def preview_items(items: Iterable[str], limit: int = 10) -> List[str]:
    """Return a friendly preview list for terminal display."""
    sorted_items = sorted(items)
    if len(sorted_items) <= limit:
        return sorted_items
    trimmed = sorted_items[:limit]
    trimmed.append(f"... +{len(sorted_items) - limit} more")
    return trimmed


def render_results(console: Any, box: Any, Table: Any, Panel: Any, results: Any) -> None:
    """Render extraction results in panel boxes."""
    summary = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="primary")
    summary.add_column("IOC Type", style="muted")
    summary.add_column("Count", justify="right", style="success")
    summary.add_row("IP addresses", str(len(results.ips)))
    summary.add_row("Domains", str(len(results.domains)))
    summary.add_row("URLs", str(len(results.urls)))

    console.print(
        Panel(
            summary,
            title="[primary]Extraction Summary[/primary]",
            border_style="accent",
            box=box.ROUNDED,
        )
    )

    for title, iocs, style in (
        ("IP Addresses", results.ips, "ioc.ip"),
        ("Domains", results.domains, "ioc.domain"),
        ("URLs", results.urls, "ioc.url"),
    ):
        table = Table(box=box.SIMPLE, show_header=True, header_style="primary")
        table.add_column(title, style=style)
        for item in preview_items(iocs, limit=12):
            table.add_row(item)

        console.print(
            Panel(
                table,
                title=f"[primary]{title}[/primary]",
                border_style="accent",
                box=box.ROUNDED,
            )
        )


def render_export_panel(
    console: Any,
    box: Any,
    Panel: Any,
    exported_files: Sequence[Path],
    log_file: Path,
) -> None:
    """Display export locations and log destination."""
    rows = [f"[success]✔[/success] {path}" for path in exported_files]
    rows.append(f"[muted]Log file:[/muted] {log_file}")
    body = "\n".join(rows)
    console.print(
        Panel(
            body,
            title="[primary]Artifacts[/primary]",
            border_style="accent",
            box=box.ROUNDED,
        )
    )


def render_error_panel(console: Any, Panel: Any, title: str, message: str) -> None:
    """Display standardized error panel."""
    console.print(Panel(message, title=title, border_style="error"))


def render_success(console: Any, message: str) -> None:
    """Display standardized success message."""
    console.print(f"[success]{message}[/success]")


def render_normalization_notes(console: Any, box: Any, Panel: Any, notes: Sequence[str]) -> None:
    """Display lightweight IOC normalization notes."""
    if not notes:
        return
    body = "\n".join(f"[muted]•[/muted] {note}" for note in notes)
    console.print(
        Panel(
            body,
            title="[primary]Normalization Notes[/primary]",
            border_style="accent",
            box=box.ROUNDED,
        )
    )
