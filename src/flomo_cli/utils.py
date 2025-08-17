from typing import Optional
from dataclasses import dataclass
# ========== Config & Models ==========
@dataclass
class Config:
    url: str
    timeout: int = 30
    verify_tls: bool = True


@dataclass
class SubmitResult:
    ok: bool
    status_code: Optional[int]
    text: str
    error: Optional[str] = None
