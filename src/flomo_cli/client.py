import requests
from .utils import SubmitResult, Config

# ========== Services ==========
class HttpClient:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    def post_content(self, content: str) -> SubmitResult:
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Accept":       "application/json, text/plain, */*",
        }
        payload = {"content": content}

        try:
            resp = requests.post(
                    self.cfg.url,
                    headers=headers,
                    json=payload,
                    timeout=self.cfg.timeout,
                    verify=self.cfg.verify_tls,
            )
        except requests.RequestException as e:
            return SubmitResult(
                    ok=False, status_code=None, text="", error=str(e)
            )

        body_preview = ""
        try:
            body_preview = resp.text
            if len(body_preview) > 2000:
                body_preview = body_preview[:2000] + "...(truncated)"
        except Exception as e:
            body_preview = f"<无法读取响应正文: {e}>"

        return SubmitResult(
                ok=200 <= resp.status_code < 300,
                status_code=resp.status_code,
                text=body_preview,
                error=None if 200 <= resp.status_code < 300 else "HTTP error",
        )
