from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme
from rich.markdown import Markdown

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


def preview_markdown(content: str) -> bool:
    # 渲染版
    md = Markdown(content, code_theme="monokai", inline_code_lexer="python")  # code_theme 可按需调整

    # 原文版，显示换行符
    # 可选：将换行显式标识
    raw_with_symbols = content.replace("\r\n", "\n").replace("\n", "⏎\n")
    raw_panel = Panel(Text(raw_with_symbols), title="原文（换行标识为 ⏎）", border_style="cyan", box=ROUNDED)

    console.print(Panel(md, title="Markdown 预览", border_style="green", box=ROUNDED))
    console.print(raw_panel)

    console.print("[info]确认发送？[y/N][/info] ", end="")
    try:
        choice = input().strip().lower()
    except EOFError:
        choice = "n"
    return choice in ("y", "yes")
