"""Optional case-level work cannot erase or delay committed population data."""

import logging
import time

from .courts import collect_courts
from .http import SourceError
from .iml_details import collect_details

log = logging.getLogger(__name__)


def collect_supplements(config, store, index, slot, *, deadline, now, collectors=None):
    collectors = collectors or {"xfer_courts": collect_courts, "iml_details": collect_details}
    states = index.setdefault("supplements", {})
    results = {}
    for name, collector in collectors.items():
        state = states.setdefault(name, {})
        if state.get("current", {}).get("slot") == slot.isoformat():
            results[name] = {"status": "already_collected"}
            continue
        state["last_attempt"] = now().isoformat()
        try:
            if deadline - time.monotonic() <= 10:
                raise SourceError("Supplemental collection deferred by the execution budget")
            point = collector(config, store, slot, deadline=deadline, now=now)
            state.update(
                current=point,
                last_success=point["finished_at"],
                error=(
                    "Some supplemental requests failed; showing the last verified records"
                    if point["failed"]
                    else "Some court reports need parser support"
                    if point.get("unsupported_files")
                    else None
                ),
            )
            results[name] = {"status": "partial" if point["failed"] else "success", **point}
        except Exception as exc:
            log.exception("%s supplemental collection failed", name)
            message = (
                str(exc)[:200]
                if isinstance(exc, SourceError)
                else f"{type(exc).__name__}: collection failed"
            )
            state["error"] = message
            results[name] = {"status": "failed", "error": message}
    return results
