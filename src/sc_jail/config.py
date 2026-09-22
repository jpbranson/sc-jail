import math
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    data_dir: Path = Path("data")
    bucket: str | None = None
    interval_seconds: int = 900
    source_timeout: float = 240
    iml_timeout: float = 420
    iml_page_workers: int = 2
    page_delay: float = 0.15
    history_days: int = 90
    detail_batch: int = 80
    detail_budget: float = 120
    detail_refresh_hours: float = 24
    court_batch: int = 8
    court_budget: float = 60
    court_verify_hours: float = 24
    user_agent: str = "ShelbyJailResearch/0.1 (+https://github.com/jpbranson)"
    xfer_dir: str = "/SCSO-InJail"
    xfer_file: str = "SCSO-InJail.xls"

    def __post_init__(self):
        if type(self.iml_page_workers) is not int or not 1 <= self.iml_page_workers <= 2:
            raise ValueError("iml_page_workers must be 1 or 2")
        for name in ("source_timeout", "iml_timeout"):
            value = getattr(self, name)
            if not math.isfinite(value) or not 0 < value <= 480:
                raise ValueError(f"{name} must be finite and between 0 and 480 seconds")
        for name in ("detail_batch", "court_batch"):
            value = getattr(self, name)
            if type(value) is not int or not 0 <= value <= 2000:
                raise ValueError(f"{name} must be an integer between 0 and 2000")
        for name in ("detail_budget", "court_budget", "detail_refresh_hours", "court_verify_hours"):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")

    @classmethod
    def from_env(cls):
        return cls(
            data_dir=Path(os.getenv("SCJ_DATA_DIR", "data")),
            bucket=os.getenv("SCJ_BUCKET") or None,
            iml_timeout=float(os.getenv("SCJ_IML_TIMEOUT_SECONDS", cls.iml_timeout)),
            iml_page_workers=int(os.getenv("SCJ_IML_PAGE_WORKERS", cls.iml_page_workers)),
            detail_batch=int(os.getenv("SCJ_DETAIL_BATCH", cls.detail_batch)),
            detail_budget=float(os.getenv("SCJ_DETAIL_BUDGET", cls.detail_budget)),
            detail_refresh_hours=float(
                os.getenv("SCJ_DETAIL_REFRESH_HOURS", cls.detail_refresh_hours)
            ),
            court_batch=int(os.getenv("SCJ_COURT_BATCH", cls.court_batch)),
            court_budget=float(os.getenv("SCJ_COURT_BUDGET", cls.court_budget)),
            court_verify_hours=float(os.getenv("SCJ_COURT_VERIFY_HOURS", cls.court_verify_hours)),
            user_agent=os.getenv("SCJ_USER_AGENT", cls.user_agent),
        )
