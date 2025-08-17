from typing import Optional
from dataclasses import dataclass
from flomo_cli.url_store import UrlStore
from flomo_cli.display import error_panel, console


# ========== Config & Models ==========
@dataclass
class Config:
    url: str
    timeout: int = 30
    verify_tls: bool = True
    debug: bool = False

    @classmethod
    def init_form_args(cls, args):
        store = UrlStore()
        final_url, wrote = store.ensure_url(args.url)
        if not final_url:
            error_panel("需要设置 URL",
                        "未检测到可用的 URL。\n"
                        "请使用 --url 指定一次，例如：\n"
                        "  flomo-cli --url https://example.com/endpoint")
            return 2

        if wrote:
            console.print(f"[info]已更新默认 URL：[/info]{final_url}")
        return cls(url=final_url, timeout=args.timeout, verify_tls=not args.insecure,
                   debug=args.debug)


@dataclass
class SubmitResult:
    ok: bool
    status_code: Optional[int]
    text: str
    error: Optional[str] = None
