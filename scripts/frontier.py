#!/usr/bin/env python3
"""Report the open-ticket frontier from flat spec.md front matter."""

import argparse
from pathlib import Path
import re
import sys


def read_metadata(path):
    """Read only the UTF-8 header, rejecting malformed or duplicate flat fields."""
    fields = {}
    with path.open("rb") as stream:
        if stream.readline().strip() != b"---":
            raise ValueError(f"{path}: missing opening front matter delimiter")

        for number, raw in enumerate(stream, 2):
            line = raw.decode("utf-8").rstrip("\r\n")
            if line.strip() == "---":
                break
            if not line.strip() or line.lstrip().startswith("#"):
                continue

            key, separator, value = line.partition(":")
            if not separator or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", key):
                raise ValueError(f"{path}:{number}: malformed field {line[:100]!r}")
            if key in fields:
                raise ValueError(f"{path}:{number}: duplicate field {key}")

            value = value.strip()
            if value.startswith(("'", '"')):
                if len(value) < 2 or value[-1] != value[0]:
                    raise ValueError(f"{path}:{number}: unterminated scalar for {key}")
                value = value[1:-1]
            elif value.startswith(("[", "{", "|", ">")):
                raise ValueError(f"{path}:{number}: {key} must be an inline scalar")
            fields[key] = value
        else:
            raise ValueError(f"{path}: unterminated front matter")

    if not fields.get("title") or fields["title"] == "null":
        raise ValueError(f"{path}: missing or empty title")
    if fields.get("status") not in ("open", "closed"):
        raise ValueError(f"{path}: status must be open or closed")
    return fields


def frontier(directory):
    """Validate every sibling edge, then render open tickets in stable bucket order."""
    if not directory.is_dir():
        raise ValueError(f"{directory}: map directory does not exist or is not a directory")

    tickets = {}
    for child in sorted(directory.iterdir()):
        path = child / "spec.md"
        if child.is_dir() and path.is_file():
            tickets[child.name] = (path, read_metadata(path))

    blockers = {slug: [] for slug in tickets}
    for slug, (path, fields) in tickets.items():
        targets = fields.get("blocks", "")
        if not targets:
            continue
        for target in sorted(set(part.strip() for part in targets.split(","))):
            if target not in tickets:
                raise ValueError(f"{path}: blocks references unknown sibling {target!r}")
            if fields["status"] == "open":
                blockers[target].append(fields["title"])

    sections = {heading: [] for heading in ("Actionable:", "Blocked:", "Claimed:", "Handoff ready:")}
    for slug, (path, fields) in tickets.items():
        if fields["status"] == "closed":
            continue
        owner = fields.get("assignee", "")
        if owner == "null":
            owner = ""

        if blockers[slug]:
            heading = "Blocked:"
        elif owner:
            heading = "Claimed:"
        elif fields.get("handover") == "ready":
            heading = "Handoff ready:"
        else:
            heading = "Actionable:"

        row = f"- {fields['title']} — {path}"
        if blockers[slug]:
            row += "; blocked by: " + ", ".join(blockers[slug])
        if owner:
            row += f"; owner: {owner}"
        sections[heading].append(row)

    output = []
    for heading, rows in sections.items():
        if rows:
            output.extend([heading, *rows])
    return "\n".join(output) if output else "No open tickets."


def main():
    """Parse the map path and emit either a complete report or a bounded diagnostic."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_directory", type=Path)
    args = parser.parse_args()

    try:
        output = frontier(args.map_directory)
    except (OSError, UnicodeError, ValueError) as error:
        diagnostic = str(error).replace("\n", " ").replace("\r", " ")
        print(f"error: {diagnostic[:500]}", file=sys.stderr)
        return 1

    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
