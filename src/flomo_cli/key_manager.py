from typing import Callable
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style  # ========== Key Bindings ==========
from pygments.lexers.markup import MarkdownLexer

class KeyBindingManager:

    def __init__(self, accept_callback: Callable[[], None], clear_callback: Callable[[], None]):
        self._kb = KeyBindings()
        self._labels: list[str] = []
        self._install_core(accept_callback, clear_callback)

    def _install_core(self, accept_callback: Callable[[], None], clear_callback: Callable[[], None]) -> None:
        # Ctrl+D: 退出
        @self._kb.add("c-d")
        def _(event):
            event.app.exit(exception=EOFError)

        # Ctrl+C: 清空输入（抛给上层捕获并清空）
        @self._kb.add("c-c")
        def _(event):
            raise KeyboardInterrupt()

        # 提交键：优先尝试 Shift+Enter（某些 ptk 版本支持）
        submitted = False
        for key in ("<s-enter>", "<s-return>"):
            try:
                self._kb.add(key)(lambda e: accept_callback())
                self._labels.append("Shift+Enter")
                submitted = True
                break
            except Exception:
                continue

        # 回退：Ctrl+J 与 Ctrl+Shift+J
        if not submitted:
            for key, label in (("c-j", "Ctrl+J"), ("c-s-j", "Ctrl+Shift+J")):
                try:
                    self._kb.add(key)(lambda e: accept_callback())
                    self._labels.append(label)
                    # 两个都留着可用
                except Exception:
                    pass

        # 可按需添加其他绑定（如清空等），目前清空通过 Ctrl+C 统一处理。

    @property
    def bindings(self) -> KeyBindings:
        return self._kb

    @property
    def submit_labels(self) -> list[str]:
        return list(dict.fromkeys(self._labels))  # 去重保持顺序


class SessionFactory:
    @staticmethod
    def build_session(key_bindings: KeyBindings) -> PromptSession:
        return PromptSession(
                multiline=True,
                key_bindings=key_bindings,
                enable_history_search=True,
                lexer=PygmentsLexer(MarkdownLexer),
                style=SessionFactory._build_style(),
                include_default_pygments_style=False,
        )

    @staticmethod
    def _build_style() -> Style:
        return Style.from_dict({
            "prompt.brackets": "ansimagenta bold",
            "prompt.label":    "ansiblue bold",
            "prompt.count":    "ansiyellow bold",
        })

    @staticmethod
    def make_prompt_fragments(counter: int):
        return [
            ("class:prompt.label", "In "),
            ("class:prompt.brackets", "["),
            ("class:prompt.count", str(counter)),
            ("class:prompt.brackets", "] "),
        ]
