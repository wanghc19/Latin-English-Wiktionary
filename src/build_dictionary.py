#!/usr/bin/env python3
"""Stream a Kaikki Latin JSONL export into Apple Dictionary XML."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


DICTIONARY_NS = "http://www.apple.com/DTDs/DictionaryService-1.0.rng"
XHTML_NS = "http://www.w3.org/1999/xhtml"
ET.register_namespace("d", DICTIONARY_NS)

GRAMMAR_MARKER = re.compile(
    r"\s+(?=(?:m|f|n|c|\?|sg|pl)(?:\s|$|\())|\s+(?=\()|;"
)
HEAD_SEPARATOR = re.compile(r"\s+or\s+", re.IGNORECASE)
CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
GENDER_TOKEN = re.compile(r"\b(m|f|n|c|\?)\b")
WIKI_ANGLE_TAG = re.compile(r"<[^<>]*>")
LEADING_GLOSS_QUALIFIER = re.compile(r"^(?:\([^()]*\)|\[[^\[\]]*\])\s*")


def clean_text(value: Any) -> str:
    """Return compact XML-safe text without changing meaningful Unicode."""
    if value is None:
        return ""
    text = CONTROL_CHARS.sub("", str(value))
    return " ".join(text.split())


def strip_diacritics(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", stripped)


def unique_nonempty(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        value = clean_text(value)
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def expansion_for(entry: dict[str, Any]) -> str:
    templates = entry.get("head_templates") or []
    if not templates:
        return ""
    return clean_text(templates[0].get("expansion"))


def fallback_head(entry: dict[str, Any]) -> str:
    """Use forms only when Wiktionary supplied no usable expansion."""
    word = clean_text(entry.get("word"))
    normalized_word = strip_diacritics(word).casefold()
    for form in entry.get("forms") or []:
        value = clean_text(form.get("form"))
        tags = form.get("tags") or []
        if (
            value
            and "canonical" in tags
            and strip_diacritics(value).casefold() == normalized_word
        ):
            return value

    templates = entry.get("head_templates") or []
    if templates:
        args = templates[0].get("args") or {}
        for key in ("head", "1", "2"):
            value = clean_text(args.get(key))
            if value:
                value = WIKI_ANGLE_TAG.sub("", value).strip("()")
                if value:
                    return value

    return word


def parse_heading(entry: dict[str, Any]) -> tuple[list[str], str, bool]:
    """Return display heads, grammatical subtitle, and fallback status."""
    expansion = expansion_for(entry)
    if not expansion:
        return [fallback_head(entry)], "", True

    marker = GRAMMAR_MARKER.search(expansion)
    if marker:
        head_phrase = expansion[: marker.start()].strip()
        subtitle = expansion[marker.start() :].strip()
        if expansion[marker.start()] == ";":
            subtitle = ";" + subtitle.lstrip(";").strip()
    else:
        head_phrase = expansion
        subtitle = ""

    heads = unique_nonempty(HEAD_SEPARATOR.split(head_phrase))
    if not heads:
        return [fallback_head(entry)], expansion, True
    return heads, subtitle, False


def add_styled_heading(parent: ET.Element, heads: list[str]) -> None:
    for index, head in enumerate(heads):
        if index:
            separator = ET.SubElement(parent, "em", {"class": "headword-separator"})
            separator.text = "or"
            separator.tail = " "
        span = ET.SubElement(parent, "span", {"class": "headword"})
        span.text = head
        if index < len(heads) - 1:
            span.tail = " "


def add_styled_subtitle(parent: ET.Element, subtitle: str) -> None:
    """Underline grammatical abbreviations while preserving visible spacing."""
    token_pattern = re.compile(r"\b(?:m|f|n|c|\?|sg|pl)\b")
    position = 0
    previous: ET.Element | None = None
    for match in token_pattern.finditer(subtitle):
        prefix = subtitle[position : match.start()]
        if previous is None:
            parent.text = (parent.text or "") + prefix
        else:
            previous.tail = (previous.tail or "") + prefix

        token = match.group(0)
        css_class = "gender" if GENDER_TOKEN.fullmatch(token) else "number"
        previous = ET.SubElement(parent, "span", {"class": css_class})
        previous.text = token
        position = match.end()

    suffix = subtitle[position:]
    if previous is None:
        parent.text = (parent.text or "") + suffix
    else:
        previous.tail = (previous.tail or "") + suffix


def gloss_path_for(sense: dict[str, Any]) -> list[str]:
    """Return Wiktextract's root-to-leaf gloss path with qualifiers intact."""
    raw_glosses = unique_nonempty(sense.get("raw_glosses") or [])
    if raw_glosses:
        return raw_glosses
    return unique_nonempty(sense.get("glosses") or [])


def without_leading_qualifiers(text: str) -> str:
    """Remove parenthesized labels only for comparing a child with its parent."""
    previous = ""
    while text != previous:
        previous = text
        text = LEADING_GLOSS_QUALIFIER.sub("", text, count=1)
    return text


def child_restates_parent(parent: str, child: str) -> bool:
    """Return whether a leaf repeats its parent after optional usage labels."""
    parent_key = parent.rstrip().rstrip(":").rstrip().casefold()
    child_key = without_leading_qualifiers(child).casefold()
    if not parent_key or not child_key.startswith(parent_key):
        return False
    if len(child_key) == len(parent_key):
        return True
    return child_key[len(parent_key)] in " \t,;:.!?()[]"


def format_gloss_path(glosses: Iterable[str]) -> str:
    """Flatten a hierarchical gloss path without repeating parent wording."""
    parts: list[str] = []
    for gloss in unique_nonempty(glosses):
        if parts and child_restates_parent(parts[-1], gloss):
            parts[-1] = gloss
        else:
            parts.append(gloss)

    if not parts:
        return ""

    definition = parts[0]
    for part in parts[1:]:
        if definition.rstrip().endswith(":"):
            definition = definition.rstrip() + " " + part
        else:
            definition += " — " + part
    return definition


def definition_for(sense: dict[str, Any]) -> str:
    gloss_path = gloss_path_for(sense)
    if gloss_path:
        return format_gloss_path(gloss_path)

    form_of = unique_nonempty(
        relation.get("word", "")
        for relation in (sense.get("form_of") or [])
        if isinstance(relation, dict)
    )
    if form_of:
        return "form of " + " or ".join(form_of)

    synonyms = unique_nonempty(
        relation.get("word", "")
        for relation in (sense.get("synonyms") or [])
        if isinstance(relation, dict)
    )
    if synonyms:
        return "synonyms: " + ", ".join(synonyms)
    return ""


def is_colon_parent_definition(parent: str, child: str) -> bool:
    """Return whether child is exactly parent followed by a colon extension."""
    parent_stem = parent.rstrip().rstrip(":").rstrip()
    child_text = child.lstrip()
    prefix = parent_stem + ":"
    return bool(
        parent_stem
        and child_text.casefold().startswith(prefix.casefold())
        and len(child_text) > len(prefix)
    )


def definitions_for_senses(
    senses: Iterable[dict[str, Any]],
) -> tuple[list[str], int]:
    """Render leaf definitions and suppress redundant colon parent senses."""
    rendered = [definition_for(sense) for sense in senses]
    definitions: list[str] = []
    suppressed = 0
    for index, definition in enumerate(rendered):
        if index + 1 < len(rendered) and is_colon_parent_definition(
            definition, rendered[index + 1]
        ):
            suppressed += 1
            continue
        if definition:
            definitions.append(definition)
    return definitions, suppressed


def index_values(entry: dict[str, Any], heads: list[str]) -> list[str]:
    values = [clean_text(entry.get("word")), *heads]
    values.extend(strip_diacritics(head) for head in heads)
    return unique_nonempty(values)


def render_entry(
    entry: dict[str, Any], line_number: int, override: dict[str, Any] | None = None
) -> tuple[str, Counter[str]]:
    stats: Counter[str] = Counter()
    word = clean_text(entry.get("word"))
    if not word:
        raise ValueError("entry has no word")

    heads, subtitle, used_fallback = parse_heading(entry)
    override = override or {}
    if override.get("heads"):
        heads = unique_nonempty(override["heads"])
        stats["overridden_heads"] += 1
    if "subtitle" in override:
        subtitle = clean_text(override["subtitle"])
        stats["overridden_subtitles"] += 1
    if used_fallback:
        stats["fallback_head"] += 1

    display_title = " or ".join(heads)
    pos = clean_text(entry.get("pos")) or "unknown"
    entry_id = f"entry-{line_number:07d}"
    node = ET.Element(
        f"{{{DICTIONARY_NS}}}entry",
        {"id": entry_id, f"{{{DICTIONARY_NS}}}title": display_title},
    )

    for value in index_values(entry, heads):
        ET.SubElement(
            node,
            f"{{{DICTIONARY_NS}}}index",
            {f"{{{DICTIONARY_NS}}}value": value},
        )

    heading = ET.SubElement(node, "h1")
    add_styled_heading(heading, heads)

    if subtitle:
        subhead = ET.SubElement(node, "p", {"class": "subhead"})
        add_styled_subtitle(subhead, subtitle)

    pos_node = ET.SubElement(node, "p", {"class": "pos"})
    pos_node.text = pos

    definitions, suppressed_colon_parents = definitions_for_senses(
        entry.get("senses") or []
    )
    stats["suppressed_colon_parent_definitions"] += suppressed_colon_parents
    if override.get("definitions"):
        definitions = unique_nonempty(override["definitions"])
        stats["overridden_definitions"] += 1
    if not definitions:
        definitions = ["Definition unavailable in the source data."]
        stats["missing_definition"] += 1

    for number, definition in enumerate(definitions, 1):
        definition_node = ET.SubElement(node, "p", {"class": "def"})
        definition_node.text = f"{number}. {definition}"

    xml = ET.tostring(node, encoding="unicode", short_empty_elements=True)
    xml = xml.replace(f' xmlns:d="{DICTIONARY_NS}"', "")
    return xml, stats


def override_key(entry: dict[str, Any]) -> str:
    return f"{clean_text(entry.get('word'))}|{clean_text(entry.get('pos'))}"


def load_overrides(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    with path.open(encoding="utf-8") as source:
        data = json.load(source)
    if not isinstance(data, dict):
        raise ValueError("overrides must be a JSON object")
    return data


def build_dictionary(
    input_path: Path,
    output_path: Path,
    report_path: Path,
    overrides_path: Path | None = None,
) -> Counter[str]:
    overrides = load_overrides(overrides_path)
    stats: Counter[str] = Counter()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open(encoding="utf-8") as source, output_path.open(
        "w", encoding="utf-8", newline="\n"
    ) as output:
        output.write('<?xml version="1.0" encoding="utf-8"?>\n')
        output.write(
            f'<d:dictionary xmlns="{XHTML_NS}" xmlns:d="{DICTIONARY_NS}">\n'
        )

        for line_number, line in enumerate(source, 1):
            if not line.strip():
                stats["blank_lines"] += 1
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                stats["invalid_json"] += 1
                continue

            try:
                xml, entry_stats = render_entry(
                    entry, line_number, overrides.get(override_key(entry))
                )
            except ValueError:
                stats["skipped_missing_word"] += 1
                continue

            output.write(xml + "\n")
            stats.update(entry_stats)
            stats["entries_written"] += 1

        output.write("</d:dictionary>\n")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as report:
        json.dump(dict(sorted(stats.items())), report, ensure_ascii=False, indent=2)
        report.write("\n")
    return stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--overrides", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stats = build_dictionary(args.input, args.output, args.report, args.overrides)
    print(json.dumps(dict(sorted(stats.items())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
