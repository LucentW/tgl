#!/usr/bin/env python3
"""
Merge multiple TL schema files into a single file suitable for tl-parser.

The tl-parser grammar expects:
  <constructors>
  ---functions---
  <functions>
  [---types---  <constructors>  ---functions---  <functions>  ...]

This script handles three input formats:
  1. Standard: ---types--- / ---functions--- blocks (scheme.tl, mtproto.tl, etc.)
  2. Layered:  ===N=== sections (encrypted_scheme.tl / TL_secret.tl)
  3. Multi-line constructors (binlog.tl — fields on separate lines, ends with ;)
"""

import re
import sys


PREAMBLE_TYPES = [
    "int ?= Int;",
    "long ?= Long;",
    "double ?= Double;",
    "string ?= String;",
    "bytes string = Bytes;",
    "int128 long long = Int128;",
    "int256 long long long long = Int256;",
]

FUNC_FIXES = {
    # req_pq without explicit hash appears in some mtproto schemas
    "req_pq nonce:int128 = ResPQ;": "req_pq#60469778 nonce:int128 = ResPQ;",
}


def combinator_name(line):
    """Canonical name for deduplication: lowercase, no hash suffix."""
    tok = line.split()[0] if line.split() else ""
    return re.sub(r"#[0-9a-f]+$", "", tok).lower()


def join_statements(text):
    """
    Yield individual TL statements.  Each statement ends with ';'.
    Multi-line constructors (binlog.tl style) are joined into a single line.
    Comment and separator lines are discarded.
    """
    buf = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("//") or line.startswith("---") or re.match(r"^===\d+===", line):
            if buf:
                # flush incomplete buffer before a section marker
                yield " ".join(buf)
                buf = []
            continue
        buf.append(line)
        if line.endswith(";"):
            yield " ".join(buf)
            buf = []
    if buf:
        yield " ".join(buf)


def parse_layered(raw):
    """Handle ===N=== format: return cumulative types (first occurrence wins)."""
    sections = re.split(r"===\d+===\n?", raw)
    seen, types = set(), []
    for s in sections[1:]:
        for stmt in join_statements(s):
            key = combinator_name(stmt)
            if key not in seen:
                seen.add(key)
                types.append(stmt)
    return types, []


def parse_standard(raw):
    """Handle standard ---types--- / ---functions--- format."""
    blocks = re.split(r"---functions---", raw)
    types_raw = re.sub(r"---types---", "", blocks[0])
    all_types = list(join_statements(types_raw))
    all_funcs = []
    for fr in blocks[1:]:
        parts = re.split(r"---types---", fr, maxsplit=1)
        all_funcs += list(join_statements(parts[0]))
        if len(parts) > 1:
            all_types += list(join_statements(parts[1]))
    return all_types, all_funcs


def parse_file(path):
    raw = open(path).read()
    if re.match(r"^\s*===\d+===", raw):
        return parse_layered(raw)
    return parse_standard(raw)


def merge(files):
    seen_t = set(combinator_name(l) for l in PREAMBLE_TYPES)
    seen_f = set()
    all_types = list(PREAMBLE_TYPES)
    all_funcs = []

    for path in files:
        t, f = parse_file(path)
        for stmt in t:
            key = combinator_name(stmt)
            if key not in seen_t:
                seen_t.add(key)
                all_types.append(stmt)
        for stmt in f:
            stmt = FUNC_FIXES.get(stmt, stmt)
            key = combinator_name(stmt)
            if key not in seen_f:
                seen_f.add(key)
                all_funcs.append(stmt)

    return all_types, all_funcs


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} file1.tl [file2.tl ...]", file=sys.stderr)
        sys.exit(1)

    all_types, all_funcs = merge(sys.argv[1:])
    print("\n".join(all_types))
    print("\n---functions---")
    print("\n".join(all_funcs))


if __name__ == "__main__":
    main()
