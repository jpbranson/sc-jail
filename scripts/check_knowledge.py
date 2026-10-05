"""Check the docs/ knowledge bundle against Open Knowledge Format (OKF) v0.2.

    python scripts/check_knowledge.py [BUNDLE]          # default: docs/
    python scripts/check_knowledge.py --entries DIR     # print index.md entries for DIR

Checks what OKF requires (every concept has parseable YAML frontmatter with a non-empty
`type`; index.md and log.md keep their reserved structure), that the optional provenance,
trust, and lifecycle fields are well formed, and this project's conventions: every concept
has a title and description, is listed in its directory's index.md with that description,
cites only `sources` ids in footnotes, and has no broken relative links. Exits 1 on any
problem. Spec: https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md
"""

import argparse
import re
import sys
from datetime import date, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
OKF_VERSION = "0.2"
RESERVED = {"index.md", "log.md"}
STATUSES = {"draft", "stable", "deprecated"}
ACTOR = re.compile(r"^(?:(?:human|process):\S+|[^\s/:]+/\S+)$")
LINK = re.compile(r"\[(?:[^\]\\]|\\.)*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
FOOTNOTE = re.compile(r"\[\^([^\]\s]+)\]")
ENTRY = re.compile(r"^[*-] \[(?P<title>[^\]]+)\]\((?P<target>[^)\s]+)\)(?: - (?P<text>.+))?$")
LOG_DATE = re.compile(r"^## (\d{4}-\d{2}-\d{2})$")
CODE = re.compile(r"^(```|~~~).*?^\1[^\n]*$|`[^`\n]+`", re.MULTILINE | re.DOTALL)


def split_frontmatter(text):
    """Return (frontmatter text or None, body)."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 3)
    if end < 0:
        return None, text
    return text[4:end + 1], text[end + 5:]


def read(path):
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def load_frontmatter(path, problems):
    raw, body = split_frontmatter(read(path))
    if raw is None:
        problems.append(f"{path}: missing YAML frontmatter")
        return None, body
    try:
        meta = yaml.safe_load(raw)
    except yaml.YAMLError as error:
        problems.append(f"{path}: frontmatter is not valid YAML: {error}".replace("\n", " "))
        return None, body
    if not isinstance(meta, dict):
        problems.append(f"{path}: frontmatter is not a mapping")
        return None, body
    return meta, body


def aware(value):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return False
    return isinstance(value, datetime) and value.utcoffset() is not None


def is_url(target):
    return re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE) is not None


def resolve(bundle, base, target):
    target = target.split("#", 1)[0].split("?", 1)[0]
    if not target:
        return None
    return bundle / target.lstrip("/") if target.startswith("/") else base / target


def check_events(path, name, value, problems):
    events = [value] if isinstance(value, dict) else value
    if not isinstance(events, list) or not events:
        problems.append(f"{path}: {name} must be a {{by, at}} mapping or a list of them")
        return
    for event in events:
        if not isinstance(event, dict) or not ACTOR.match(str(event.get("by", ""))):
            problems.append(f"{path}: {name} entry needs `by` in the actor convention")
        elif "at" in event and not aware(event["at"]):
            problems.append(f"{path}: {name}.at must be an ISO 8601 datetime with an offset")
        elif name == "verified" and "at" not in event:
            problems.append(f"{path}: verified entry needs `at`")


def check_concept(bundle, path, problems):
    meta, body = load_frontmatter(path, problems)
    if meta is None:
        return None
    if not isinstance(meta.get("type"), str) or not meta["type"].strip():
        problems.append(f"{path}: `type` is required and must be a non-empty string")
    for key in ("title", "description"):
        if not isinstance(meta.get(key), str) or not meta[key].strip():
            problems.append(f"{path}: `{key}` is required by this bundle's conventions")
    if "\n" in str(meta.get("description", "")):
        problems.append(f"{path}: description must be a single line")
    tags = meta.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(t, str) and t for t in tags):
        problems.append(f"{path}: tags must be a list of strings")
    if meta.get("status", "stable") not in STATUSES:
        problems.append(f"{path}: status must be one of {sorted(STATUSES)}")
    if "stale_after" in meta and not aware(meta["stale_after"]):
        problems.append(f"{path}: stale_after must be an ISO 8601 datetime with an offset")
    if "generated" in meta:
        if isinstance(meta["generated"], list):
            problems.append(f"{path}: generated must be a single {{by, at}} mapping")
        else:
            check_events(path, "generated", meta["generated"], problems)
    if "verified" in meta:
        check_events(path, "verified", meta["verified"], problems)
    resource = meta.get("resource")
    if resource is not None and not isinstance(resource, str):
        problems.append(f"{path}: resource must be a string")
    elif resource and not is_url(resource) and not resolve(bundle, path.parent, resource).exists():
        problems.append(f"{path}: resource {resource} does not exist")
    ids = check_sources(bundle, path, meta, problems)
    text = CODE.sub("", body)
    for label in sorted(set(FOOTNOTE.findall(text)) - ids):
        problems.append(f"{path}: footnote [^{label}] has no matching sources id")
    check_links(bundle, path, text, problems)
    return meta


def check_sources(bundle, path, meta, problems):
    sources = meta.get("sources", [])
    if not isinstance(sources, list):
        problems.append(f"{path}: sources must be a list")
        return set()
    ids = set()
    for source in sources:
        if not isinstance(source, dict) or not isinstance(source.get("resource"), str):
            problems.append(f"{path}: every sources entry needs a `resource`")
            continue
        if "id" in source:
            if source["id"] in ids:
                problems.append(f"{path}: duplicate sources id {source['id']}")
            ids.add(str(source["id"]))
        if "last_modified" in source and not aware(source["last_modified"]):
            problems.append(f"{path}: sources last_modified must be a datetime with an offset")
        count = source.get("usage_count", 0)
        if not isinstance(count, int) or count < 0:
            problems.append(f"{path}: usage_count must be a non-negative integer")
    for window in [meta.get("usage_window")] + [s.get("usage_window") for s in sources
                                                if isinstance(s, dict)]:
        if window is not None and not (isinstance(window, dict)
                                       and aware(window.get("from")) and aware(window.get("to"))):
            problems.append(f"{path}: usage_window needs `from` and `to` datetimes")
    return ids


def check_links(bundle, path, text, problems):
    for target in LINK.findall(text):
        if is_url(target) or target.startswith("#"):
            continue
        resolved = resolve(bundle, path.parent, target)
        if resolved is not None and not resolved.exists():
            problems.append(f"{path}: broken link {target}")


def check_index(bundle, directory, concepts, problems):
    path = directory / "index.md"
    if not path.exists():
        problems.append(f"{path}: missing; every directory with concepts needs one")
        return
    raw, body = split_frontmatter(read(path))
    if raw is not None:
        meta = yaml.safe_load(raw) if directory == bundle else None
        if directory != bundle or meta != {"okf_version": OKF_VERSION}:
            problems.append(f"{path}: index frontmatter is only allowed at the bundle root, "
                            f"as okf_version: \"{OKF_VERSION}\"")
    elif directory == bundle:
        problems.append(f"{path}: root index should declare okf_version: \"{OKF_VERSION}\"")
    listed = set()
    for number, line in enumerate(body.splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        entry = ENTRY.match(line)
        if not entry:
            problems.append(f"{path}:{number}: index lines are headings or "
                            "`* [Title](link) - description` entries")
            continue
        target = resolve(bundle, directory, entry["target"])
        if target is None or not target.exists():
            problems.append(f"{path}:{number}: broken link {entry['target']}")
            continue
        target = target.resolve()
        listed.add(target / "index.md" if target.is_dir() else target)
        meta = concepts.get(target)
        if meta and entry["text"] != meta.get("description"):
            problems.append(f"{path}:{number}: description differs from "
                            f"{target.name}'s frontmatter")
    for child in sorted(directory.iterdir()):
        if child.is_dir() and any(child.rglob("*.md")):
            if (child / "index.md").resolve() not in listed:
                problems.append(f"{path}: subdirectory {child.name}/ is not listed")
        elif child.suffix == ".md" and child.name not in RESERVED:
            if child.resolve() not in listed:
                problems.append(f"{path}: concept {child.name} is not listed")


def check_log(path, problems):
    raw, body = split_frontmatter(read(path))
    if raw is not None:
        problems.append(f"{path}: log.md takes no frontmatter")
    dates = []
    for number, line in enumerate(body.splitlines(), 1):
        if line.startswith("## "):
            match = LOG_DATE.match(line)
            try:
                dates.append(date.fromisoformat(match[1]))
            except (TypeError, ValueError):
                problems.append(f"{path}:{number}: date headings must be ## YYYY-MM-DD")
    if dates != sorted(set(dates), reverse=True):
        problems.append(f"{path}: date headings must be unique and newest first")


def check_bundle(bundle):
    bundle = Path(bundle).resolve()
    problems, concepts = [], {}
    for path in sorted(bundle.rglob("*.md")):
        if path.name == "log.md":
            check_log(path, problems)
        elif path.name != "index.md":
            concepts[path.resolve()] = check_concept(bundle, path, problems)
    directories = {p.parent for p in concepts} | {p.parent for p in bundle.rglob("log.md")}
    for directory in sorted(directories | {bundle}):
        check_index(bundle, directory, concepts, problems)
    return [str(p).replace(str(bundle) + "\\", "").replace(str(bundle) + "/", "")
            for p in problems], len(concepts)


def entries(directory):
    for path in sorted(Path(directory).glob("*.md")):
        if path.name not in RESERVED:
            meta, _ = load_frontmatter(path, [])
            if meta:
                print(f"* [{meta.get('title', path.stem)}]({path.name}) - "
                      f"{meta.get('description', '')}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("bundle", nargs="?", default=ROOT / "docs", type=Path)
    parser.add_argument("--entries", type=Path, help="print index entries for one directory")
    args = parser.parse_args(argv)
    if args.entries:
        entries(args.entries)
        return 0
    problems, count = check_bundle(args.bundle)
    for problem in problems:
        print(problem)
    print(f"{count} concepts, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
