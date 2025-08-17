#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import signal
import argparse
from typing import Optional, Sequence
from prompt_toolkit.document import Document
from prompt_toolkit.application.current import get_app
from pygments.lexers.markup import MarkdownLexer

from rich.panel import Panel
from rich.text import Text

from flomo_cli.key_manager import KeyBindingManager
from flomo_cli.client import HttpClient
from flomo_cli.key_manager import SessionFactory
from flomo_cli.utils import Config
from flomo_cli.display import console, error_panel
from flomo_cli.url_store import UrlStore


# ========== Application Orchestrator ==========
class App:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.http = HttpClient(cfg)

        self._pending_text: Optional[str] = None

        def accept():
            app = get_app()
            buf = app.current_buffer
            app.exit(result=buf.text)

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
                console.print("[warn] Input cancelled.（Ctrl+C）[/warn]")
                try:
                    app = get_app()
                    app.current_buffer.document = Document(text="")
                except Exception:
                    pass
                continue
            except EOFError:
                console.print("\n[info]Exited.（Ctrl+D）[/info]")
                break
            except Exception as e:
                console.print(Panel.fit(Text(repr(e), no_wrap=False), title="Unexpected error !", border_style="red"))
                self.counter += 1
                continue

    def _handle_result(self, result):
        if result.ok:
            if self.cfg.debug:
                console.print(Panel.fit(
                        Text(f"Status: {result.status_code}\nResponse: {result.text}", no_wrap=False),
                        title="Success", border_style="green"
                ))
            else:
                console.print(Text(text="Create memos success !"))
        else:
            if result.status_code is None:
                # 网络层异常
                console.print(Panel.fit(
                        Text(result.error or "Request failed !", no_wrap=False),
                        title="Network error.", border_style="red"
                ))
            else:
                # HTTP 非 2xx
                console.print(Panel.fit(
                        Text(f"Status: {result.status_code}\nResponse: {result.text}", no_wrap=False),
                        title="Send error.", border_style="red"
                ))

    # ========== Internal helpers ==========
    def _handle_submit(self, content: str):
        console.print(f"[info]Add memo to ->[/info] {self.cfg.url}")
        result = self.http.post_content(content)
        self._handle_result(result)

    def _print_banner(self):
        submit_hint = "、".join(self.kbm.submit_labels) or "Ctrl+J"
        console.rule("[info]Start[/info]")
        console.print(Panel.fit(
                Text(
                        "Descriptions：\n"
                        f" - Submit：{submit_hint}\n"
                        " - Cancel：Ctrl+C\n"
                        " - Exit：Ctrl+D\n\n"
                        "You can paste content from other app to here, multi-line markdown style text is support !",
                        no_wrap=False
                ),
                title="Help", border_style="cyan"
        ))
        console.print(f"[info]Your flomo api：[/info]{self.cfg.url}")
        if not self.cfg.verify_tls:
            console.print("[warn] Disable tls verification !（--insecure）[/warn]")


# ========== CLI ==========
def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
            description="flomo-cli: Memo any memory to flomo for cli!"
    )
    parser.add_argument("--url",
                        help="Your flomo api, once config, anytime use in ~/.flomo.cli.toml")
    parser.add_argument("--timeout", type=int, default=30, help="Max timeout.")
    parser.add_argument("--insecure", action="store_true", help="Whether disable tls.")
    parser.add_argument("--debug", "-d", action="store_true", help="Start with debug mode.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    args = parse_args(argv)
    cfg = Config.init_form_args(args)
    app = App(cfg)
    app.run()
    return 0


if __name__ == "__main__":
    main()
