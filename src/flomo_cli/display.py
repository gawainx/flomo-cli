from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme

# ========== UI Theme ==========
custom_theme = Theme({
    "ok":   "bold green",
    "warn": "bold yellow",
    "err":  "bold red",
    "info": "bold cyan",
}) if Theme else None
console = Console(theme=custom_theme) if custom_theme else Console()


def info_panel(title: str, msg: str, style: str = "cyan"):
    console.print(Panel.fit(Text(msg, no_wrap=False), title=title, border_style=style))


def warn_panel(title: str, msg: str):
    info_panel(title, msg, style="yellow")


def error_panel(title: str, msg: str):
    info_panel(title, msg, style="red")


def print_rule(title: Optional[str] = None):
    if title:
        console.rule(f"[info]{title}[/info]")
    else:
        console.rule()
