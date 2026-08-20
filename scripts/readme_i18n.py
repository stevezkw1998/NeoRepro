#!/usr/bin/env python3
"""Track and validate localized README files without calling a translation model."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "README.md"
STATE = ROOT / "i18n" / "readme_state.json"

LOCALES = {
    "zh-CN": ROOT / "README.zh-CN.md",
    "zh-TW": ROOT / "README.zh-TW.md",
    "ja": ROOT / "README.ja.md",
    "ko": ROOT / "README.ko.md",
    "de": ROOT / "README.de.md",
    "es": ROOT / "README.es.md",
    "fr": ROOT / "README.fr.md",
}

NAVIGATION = (
    "[English](README.md) | [简体中文](README.zh-CN.md) | "
    "[繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | "
    "[한국어](README.ko.md) | [Deutsch](README.de.md) | "
    "[Español](README.es.md) | [Français](README.fr.md)"
)

PROTECTED_TOKENS = (
    "NeoRepro",
    "MHC-I",
    "MHCflurry",
    "BigMHC",
    "PRIME",
    "DeepImmuno-CNN",
    "DeepHLApan",
    "TESLA",
    "IMPROVE",
    "Zhao",
    "AUROC",
    "NDCG@5",
    "Recall@20",
    "Top-K",
    "SHA-256",
    "CITATION.cff",
    "CPython",
    "Apple Silicon",
    "MIT",
)

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
CODE_RE = re.compile(r"```[^\n]*\n.*?```", re.DOTALL)
NUMBER_RE = re.compile(r"(?<![A-Za-z0-9])(?:v)?\d+(?:[.,]\d+)*(?:%|e-\d+)?")


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value or "section"


def split_sections(text: str, *, source: bool) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    current: list[str] = []
    current_id = "preamble"
    section_index = 0
    for line in text.splitlines(keepends=True):
        if line.startswith("## "):
            sections.append((current_id, "".join(current)))
            current = [line]
            section_index += 1
            current_id = slug(line[3:].strip()) if source else f"section-{section_index}"
        else:
            current.append(line)
    sections.append((current_id, "".join(current)))
    return sections


def source_snapshot() -> tuple[str, list[tuple[str, str]], dict[str, str]]:
    text = SOURCE.read_text(encoding="utf-8")
    sections = split_sections(text, source=True)
    hashes = {section_id: digest(body) for section_id, body in sections}
    return text, sections, hashes


def load_state() -> dict[str, object]:
    if not STATE.exists():
        return {"version": 1, "locales": {}}
    return json.loads(STATE.read_text(encoding="utf-8"))


def link_targets(text: str) -> list[str]:
    return LINK_RE.findall(text)


def numbers(text: str) -> Counter[str]:
    return Counter(NUMBER_RE.findall(text))


def validate_content(
    locale: str, source_text: str, source_sections: list[tuple[str, str]]
) -> list[str]:
    path = LOCALES[locale]
    if not path.exists():
        return [f"missing {path.name}"]

    translated = path.read_text(encoding="utf-8")
    errors: list[str] = []
    first_line = translated.splitlines()[0] if translated.splitlines() else ""
    if first_line != NAVIGATION:
        errors.append("language navigation differs from README.md")
    if "# NeoRepro" not in translated:
        errors.append("missing '# NeoRepro' title")

    target_sections = split_sections(translated, source=False)
    if len(target_sections) != len(source_sections):
        errors.append(
            f"section count differs: source={len(source_sections)} target={len(target_sections)}"
        )
    if link_targets(translated) != link_targets(source_text):
        errors.append("Markdown link targets or their order differ")
    if CODE_RE.findall(translated) != CODE_RE.findall(source_text):
        errors.append("fenced code blocks differ")
    if numbers(translated) != numbers(source_text):
        errors.append("numeric tokens differ")

    for token in PROTECTED_TOKENS:
        if translated.count(token) != source_text.count(token):
            errors.append(f"protected token count differs: {token}")

    for target in link_targets(translated):
        if target.startswith(("http://", "https://", "#")):
            continue
        local_target = target.split("#", 1)[0]
        if local_target and not (ROOT / local_target).exists():
            errors.append(f"broken relative link: {target}")
    return errors


def outdated_sections(locale: str, hashes: dict[str, str], state: dict[str, object]) -> list[str]:
    locales = state.get("locales", {})
    if not isinstance(locales, dict):
        return list(hashes)
    locale_state = locales.get(locale, {})
    if not isinstance(locale_state, dict):
        return list(hashes)
    recorded = locale_state.get("sections", {})
    if not isinstance(recorded, dict):
        return list(hashes)
    return [section_id for section_id, value in hashes.items() if recorded.get(section_id) != value]


def command_status() -> int:
    _, _, hashes = source_snapshot()
    state = load_state()
    for locale, path in LOCALES.items():
        if not path.exists():
            print(f"{locale}: missing {path.name}")
            continue
        stale = outdated_sections(locale, hashes, state)
        print(f"{locale}: {'current' if not stale else 'outdated: ' + ', '.join(stale)}")
    return 0


def command_check() -> int:
    source_text, source_sections, hashes = source_snapshot()
    state = load_state()
    failures: list[str] = []
    if source_text.splitlines()[0] != NAVIGATION:
        failures.append("README.md: canonical language navigation is missing or changed")

    for locale in LOCALES:
        for message in validate_content(locale, source_text, source_sections):
            failures.append(f"{locale}: {message}")
        stale = outdated_sections(locale, hashes, state)
        if stale:
            failures.append(f"{locale}: translations are stale for {', '.join(stale)}")

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 1
    print(f"README translations are synchronized and valid for {len(LOCALES)} locales.")
    return 0


def command_stamp(selected: list[str]) -> int:
    source_text, source_sections, hashes = source_snapshot()
    locales = list(LOCALES) if selected == ["all"] else selected
    unknown = [locale for locale in locales if locale not in LOCALES]
    if unknown:
        print(f"ERROR: unknown locales: {', '.join(unknown)}", file=sys.stderr)
        return 2

    failures: list[str] = []
    for locale in locales:
        for message in validate_content(locale, source_text, source_sections):
            failures.append(f"{locale}: {message}")
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 1

    state = load_state()
    locale_state = state.setdefault("locales", {})
    if not isinstance(locale_state, dict):
        print("ERROR: malformed locale state", file=sys.stderr)
        return 2
    state["version"] = 1
    state["source"] = SOURCE.name
    state["source_sha256"] = digest(source_text)
    for locale in locales:
        locale_state[locale] = {"file": LOCALES[locale].name, "sections": hashes}
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Stamped {len(locales)} locale(s) against the current README.md.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status", help="show which English sections need translation")
    subparsers.add_parser("check", help="validate structure, protected content, and freshness")
    stamp = subparsers.add_parser("stamp", help="record reviewed translations as synchronized")
    stamp.add_argument("--locale", nargs="+", default=["all"], choices=["all", *LOCALES])
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "status":
        return command_status()
    if args.command == "check":
        return command_check()
    return command_stamp(args.locale)


if __name__ == "__main__":
    raise SystemExit(main())
