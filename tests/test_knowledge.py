import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_knowledge", ROOT / "scripts" / "check_knowledge.py"
)
check_knowledge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_knowledge)

CONCEPT = """---
type: Metric
title: IML population
description: Distinct permanent IDs held.
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-05T00:00:00Z }
verified: { by: human:owner, at: 2026-10-05T01:00:00Z }
sources:
  - id: readme
    resource: https://example.com/README.md
---

Counts people, not bookings.[^readme] See [the overview](../overview.md).

[^readme]: README
"""


def bundle(tmp_path, **files):
    defaults = {
        "index.md": '---\nokf_version: "0.2"\n---\n\n# Start\n\n'
                    "* [Overview](overview.md) - What this is.\n"
                    "* [Measures](measures/) - Definitions.\n",
        "log.md": "# Update log\n\n## 2026-10-05\n* **Creation**: Bundle.\n\n## 2026-09-19\n"
                  "* **Initialization**: Started.\n",
        "overview.md": "---\ntype: Project Overview\ntitle: Overview\n"
                       "description: What this is.\n---\n\nText.\n",
        "measures/index.md": "# Measures\n\n"
                             "* [IML population](iml.md) - Distinct permanent IDs held.\n",
        "measures/iml.md": CONCEPT,
    }
    for name, text in {**defaults, **files}.items():
        if text is None:
            continue
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return check_knowledge.check_bundle(tmp_path)


def test_a_conformant_bundle_has_no_problems(tmp_path):
    problems, count = bundle(tmp_path)
    assert problems == []
    assert count == 2


def test_missing_type_unlisted_concept_and_broken_link_are_reported(tmp_path):
    problems, _ = bundle(
        tmp_path,
        **{"measures/extra.md": "---\ntitle: Extra\ndescription: Extra.\n---\n\n"
                                "[gone](../missing.md)\n"},
    )
    text = "\n".join(problems)
    assert "`type` is required" in text
    assert "concept extra.md is not listed" in text
    assert "broken link ../missing.md" in text


def test_index_descriptions_must_match_frontmatter(tmp_path):
    problems, _ = bundle(
        tmp_path, **{"measures/index.md": "# Measures\n\n* [IML population](iml.md) - Old.\n"}
    )
    assert any("description differs" in p for p in problems)


def test_trust_and_provenance_fields_are_validated(tmp_path):
    concept = (CONCEPT.replace("at: 2026-10-05T01:00:00Z", "at: 2026-10-05T01:00:00")
               .replace("id: readme", "id: other"))
    problems, _ = bundle(tmp_path, **{"measures/iml.md": concept})
    text = "\n".join(problems)
    assert "verified.at must be an ISO 8601 datetime with an offset" in text
    assert "footnote [^readme] has no matching sources id" in text


def test_log_dates_must_be_newest_first(tmp_path):
    problems, _ = bundle(
        tmp_path, **{"log.md": "# Log\n\n## 2026-09-19\n* a\n\n## 2026-10-05\n* b\n"}
    )
    assert any("newest first" in p for p in problems)


def test_index_frontmatter_is_only_okf_version_at_the_root(tmp_path):
    problems, _ = bundle(
        tmp_path,
        **{"measures/index.md": '---\nokf_version: "0.2"\n---\n\n'
                                "* [IML population](iml.md) - Distinct permanent IDs held.\n"},
    )
    assert any("only allowed at the bundle root" in p for p in problems)


@pytest.mark.skipif(not (ROOT / "docs" / "index.md").exists(),
                    reason="docs/ is not part of the Cloud Build context")
def test_the_project_knowledge_bundle_is_conformant():
    problems, count = check_knowledge.check_bundle(ROOT / "docs")
    assert problems == []
    assert count > 0
