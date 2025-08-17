import sys, os
import toml
from typing import Optional, Sequence
from pathlib import Path
from flomo_cli.display import console, Panel, Text
from flomo_cli.const import *


class UrlStore:
    """
    在项目源码目录（运行的 main.py 所在目录）下维护 .flomo.cli.toml
    用户无需指定路径；首次写入或覆盖时给予提示，保留知情权。
    """

    def __init__(self, filename: str = CONFIG_FILENAME, section: str = CONFIG_SECTION, key: str = CONFIG_KEY_URL):
        self.filename = filename
        self.section = section
        self.key = key
        # 以 main.py 所在目录为根目录
        self.base_dir = self._resolve_project_dir()
        self.path = os.path.join(self.base_dir, self.filename)

    def _resolve_project_dir(self) -> str:
        """
        使用用户 Home 目录作为配置文件所在目录。
        例如：
        - macOS/Linux: /Users/xxx 或 /home/xxx
        - Windows: C:\\Users\\xxx
        """
        return str(Path.home())

    def load(self) -> Optional[str]:
        if not os.path.exists(self.path):
            return None
        try:
            data = toml.load(self.path)
            return data.get(self.section, {}).get(self.key) or None
        except Exception as e:
            console.print(Panel.fit(Text(f"读取配置失败：{e}", no_wrap=False), title="配置错误", border_style="red"))
            return None

    def save(self, url: str) -> bool:
        # 写入前提示用户（仅提示，不要求确认）：说明将写入项目目录的隐藏文件
        console.print(Panel.fit(
                Text(
                        f"将把 URL 写入本项目目录下的配置文件：\n"
                        f"{self.path}\n\n",
                        no_wrap=False,
                ),
                title="写入配置", border_style="cyan",
        ))
        try:
            data = {}
            if os.path.exists(self.path):
                try:
                    data = toml.load(self.path) or {}
                except Exception:
                    data = {}
            if self.section not in data:
                data[self.section] = {}
            data[self.section][self.key] = url
            # 确保目录存在（通常源码目录存在，这里谨慎处理）
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                toml.dump(data, f)
            return True
        except Exception as e:
            console.print(Panel.fit(Text(f"写入配置失败：{e}", no_wrap=False), title="错误", border_style="red"))
            return False

    def confirm_overwrite(self, old_url: str, new_url: str) -> bool:
        console.print(Panel.fit(
                Text(
                        "检测到你通过 --url 指定了一个与现有配置不同的地址：\n\n"
                        f"现有: {old_url}\n"
                        f"新值: {new_url}\n\n"
                        "是否覆盖并保存为默认？[y/N] ",
                        no_wrap=False
                ),
                title="覆盖确认", border_style="yellow",
        ))
        try:
            # 用 input 获取一次性确认，不走 prompt_toolkit，以免污染会话
            choice = input().strip().lower()
        except EOFError:
            choice = "n"
        return choice in ("y", "yes")

    def ensure_url(self, cli_url: Optional[str]) -> tuple[Optional[str], bool]:
        """
        确定最终 URL：
        - 若 cli_url 为 None：
            - 若文件存在，返回文件中的 URL
            - 否则返回 (None, False) 以提示用户必须指定
        - 若 cli_url 非 None：
            - 若文件不存在：写入并返回 (cli_url, True)
            - 若文件存在且不同：提示覆盖；如确认则写入并返回 (cli_url, True)，否则返回(旧值, False)
            - 若相同：返回 (cli_url, False)
        返回 (final_url, wrote_flag)
        """
        current = self.load()
        if cli_url is None:
            if current:
                return current, False
            else:
                return None, False
        # cli 指定了 url
        if not current:
            ok = self.save(cli_url)
            return (cli_url if ok else None), ok
        if current != cli_url:
            if self.confirm_overwrite(current, cli_url):
                ok = self.save(cli_url)
                return (cli_url if ok else current), ok
            else:
                console.print("[warn]已取消覆盖操作，将继续使用现有配置中的 URL[/warn]")
                return current, False
        # 相同，无需写入
        return cli_url, False
