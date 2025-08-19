#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import signal
import click
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


# ========== CLI with Click ==========

@click.group()
@click.option("--url", help="Your flomo api, once config, anytime use in ~/.flomo.cli.toml")
@click.option("--timeout", type=int, default=30, show_default=True, help="Max timeout.")
@click.option("--insecure", is_flag=True, help="Whether disable tls.")
@click.option("--debug", "-d", is_flag=True, help="Start with debug mode.")
@click.pass_context
def cli(ctx, url, timeout, insecure, debug):
    """
    flomo-cli: Memo any memory to flomo for cli!
    """
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    # Simulate argparse.Namespace for Config.init_form_args
    class Args:
        pass
    args = Args()
    args.url = url
    args.timeout = timeout
    args.insecure = insecure
    args.debug = debug
    cfg = Config.init_form_args(args)
    ctx.obj = {"cfg": cfg}

@cli.command("run")
@click.pass_context
def run_cmd(ctx):
    """Start the flomo CLI app."""
    cfg = ctx.obj["cfg"]
    app = App(cfg)
    app.run()

def main():
    cli(prog_name="flomo-cli")

if __name__ == "__main__":
    main()
