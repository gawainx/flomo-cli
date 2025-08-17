#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import signal
import argparse
from typing import Optional, Sequence, Callable

from flomo_cli.key_manager import KeyBindingManager
from flomo_cli.client import HttpClient
from flomo_cli.key_manager import SessionFactory
from flomo_cli.utils import Config

from prompt_toolkit.document import Document
from prompt_toolkit.application.current import get_app
from pygments.lexers.markup import MarkdownLexer

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


# ========== Application Orchestrator ==========
class App:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.http = HttpClient(cfg)

        # 先占位，声明将由 KeyBindingManager 回调提交
        self._pending_text: Optional[str] = None  # 不直接用；PromptSession 通过 app.exit(...) 返回文本

        # 接受提交：调用 prompt_toolkit 的 exit，返回当前缓冲文本
        def accept():
            # 交给 PromptSession 的 prompt() 通过 app.exit(result=...) 结束本次循环
            app = get_app()
            buf = app.current_buffer
            app.exit(result=buf.text)

        # 清空回调：抛出 KeyboardInterrupt 交由上层处理
        def clear():
            raise KeyboardInterrupt()

        self.kbm = KeyBindingManager(accept_callback=accept, clear_callback=clear)
        self.session = SessionFactory.build_session(self.kbm.bindings)
        self.counter = 1

    def run(self):
        self._print_banner()

        while True:
            try:
                text = self.session.prompt(SessionFactory.make_prompt_fragments(self.counter))
                self._handle_submit(text)
                self.counter += 1
            except KeyboardInterrupt:
                console.print("[warn]已取消本次输入（Ctrl+C）[/warn]")
                # 清空当前输入缓冲
                try:
                    app = get_app()
                    app.current_buffer.document = Document(text="")
                except Exception:
                    pass
                continue
            except EOFError:
                console.print("\n[info]已退出（Ctrl+D）[/info]")
                break
            except Exception as e:
                console.print(Panel.fit(Text(repr(e), no_wrap=False), title="未预期错误", border_style="red"))
                self.counter += 1
                continue

    # ========== Internal helpers ==========
    def _handle_submit(self, content: str):
        console.print(f"[info]发送 POST ->[/info] {self.cfg.url}")
        result = self.http.post_content(content)

        if result.ok:
            console.print(Panel.fit(
                    Text(f"状态: {result.status_code}\n响应: {result.text}", no_wrap=False),
                    title="发送成功", border_style="green"
            ))
        else:
            if result.status_code is None:
                # 网络层异常
                console.print(Panel.fit(
                        Text(result.error or "请求失败", no_wrap=False),
                        title="网络错误", border_style="red"
                ))
            else:
                # HTTP 非 2xx
                console.print(Panel.fit(
                        Text(f"状态: {result.status_code}\n响应: {result.text}", no_wrap=False),
                        title="发送失败", border_style="red"
                ))

    def _print_banner(self):
        submit_hint = "、".join(self.kbm.submit_labels) or "Ctrl+J"
        console.rule("[info]启动[/info]")
        console.print(Panel.fit(
                Text(
                        "说明：\n"
                        f" - 提交：{submit_hint}\n"
                        " - 取消当前输入：Ctrl+C\n"
                        " - 退出程序：Ctrl+D\n\n"
                        "提示：支持粘贴大段 Markdown，中英文标点与换行将被原样发送",
                        no_wrap=False
                ),
                title="使用帮助", border_style="cyan"
        ))
        console.print(f"[info]目标 URL：[/info]{self.cfg.url}")
        if not self.cfg.verify_tls:
            console.print("[warn]已禁用 TLS 证书校验（--insecure）[/warn]")


# ========== CLI ==========
def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
            description="多行输入 -> POST JSON(content=...) 发送工具"
    )
    parser.add_argument("--url", required=True, help="目标 POST URL")
    parser.add_argument("--timeout", type=int, default=30, help="请求超时（秒）")
    parser.add_argument("--insecure", action="store_true", help="忽略 TLS 证书校验")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None):
    args = parse_args(argv)
    cfg = Config(url=args.url, timeout=args.timeout, verify_tls=not args.insecure)

    # 确保 Ctrl+C 能被 prompt_toolkit 捕捉
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, signal.SIG_DFL)

    app = App(cfg)
    app.run()


if __name__ == "__main__":
    main()
