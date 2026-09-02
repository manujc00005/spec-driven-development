"""A deliberately tiny, strict YAML subset parser.

Spec 040 FR-003 requires the verdict/completion parser to fail closed. A full
YAML parser is the wrong tool for that: it accepts anchors, aliases, tags, flow
collections, multi-document streams and implicit type coercion, all of which
widen the shape of "valid" far past what spec 031 FR-003/FR-004 define. This
module accepts ONLY the grammar those FRs use and rejects everything else, so
"unrecognized" and "rejected" are the same thing by construction.

Accepted grammar:

    key: scalar
    key: []
    key:
      - scalar
      - key: scalar
        key: scalar

Rejected on sight: anchors (&), aliases (*), tags (!), flow mappings ({), flow
sequences other than the literal empty `[]`, document markers (---, ...),
multi-line scalars (|, >), tabs, and any nesting deeper than the one level the
schema uses.
"""


class MiniYamlError(ValueError):
    """The document is outside the accepted subset. Always fail closed on this."""


_FORBIDDEN_VALUE_PREFIXES = ("&", "*", "!", "|", ">", "{")


def _strip_comment(raw: str) -> str:
    """Remove a trailing ` # comment`, respecting quotes.

    The canonical block in skills/sdd-orchestrate/SKILL.md carries an inline
    comment (`verdict: APPROVE # APPROVE | REJECT`), so this is required, not a
    convenience.
    """
    out = []
    quote = None
    i = 0
    while i < len(raw):
        ch = raw[i]
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
            out.append(ch)
        elif ch == "#" and (i == 0 or raw[i - 1] in (" ", "\t")):
            break
        else:
            out.append(ch)
        i += 1
    if quote:
        raise MiniYamlError("unterminated quoted string")
    return "".join(out).rstrip()


def _scalar(raw: str) -> str:
    v = raw.strip()
    if not v:
        raise MiniYamlError("empty scalar")
    if v[0] in ("'", '"'):
        if len(v) < 2 or v[-1] != v[0]:
            raise MiniYamlError("unterminated quoted scalar")
        return v[1:-1]
    if v.startswith(_FORBIDDEN_VALUE_PREFIXES):
        raise MiniYamlError("value uses an unsupported YAML feature: %r" % v[0])
    return v


def _split_key(line: str):
    """Split `key: value` -> (key, value_or_None). Returns None when not a mapping line."""
    idx = line.find(":")
    if idx == -1:
        return None
    key = line[:idx].strip()
    if not key or any(c in key for c in " \t"):
        return None
    return key, line[idx + 1 :].strip()


def parse(text: str) -> dict:
    """Parse the accepted subset into a dict. Raise MiniYamlError on anything else."""
    if "\t" in text:
        raise MiniYamlError("tabs are not accepted")

    lines = []
    for n, raw in enumerate(text.splitlines(), 1):
        if raw.lstrip().startswith("#") or not raw.strip():
            continue
        if raw.strip() in ("---", "..."):
            raise MiniYamlError("document markers are not accepted")
        stripped = _strip_comment(raw)
        if not stripped.strip():
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        lines.append((n, indent, stripped.strip()))

    doc = {}
    i = 0
    while i < len(lines):
        n, indent, content = lines[i]
        if indent != 0:
            raise MiniYamlError("line %d: unexpected indentation at top level" % n)
        split = _split_key(content)
        if split is None:
            raise MiniYamlError("line %d: not a mapping entry: %r" % (n, content))
        key, value = split
        if key in doc:
            raise MiniYamlError("line %d: duplicate key %r" % (n, key))
        if value == "[]":
            doc[key] = []
            i += 1
            continue
        if value:
            doc[key] = _scalar(value)
            i += 1
            continue
        # Block sequence expected.
        items, i = _parse_sequence(lines, i + 1)
        doc[key] = items
    if not doc:
        raise MiniYamlError("empty document")
    return doc


def _parse_sequence(lines, i):
    items = []
    seq_indent = None
    while i < len(lines):
        n, indent, content = lines[i]
        if indent == 0:
            break
        if not content.startswith("- "):
            raise MiniYamlError("line %d: expected a sequence item, got %r" % (n, content))
        if seq_indent is None:
            seq_indent = indent
        elif indent != seq_indent:
            raise MiniYamlError("line %d: inconsistent sequence indentation" % n)
        body = content[2:].strip()
        split = _split_key(body)
        if split is None:
            items.append(_scalar(body))
            i += 1
            continue
        # Mapping item: this line plus any deeper-indented continuation lines.
        entry = {}
        key, value = split
        entry[key] = _scalar(value) if value != "[]" else []
        i += 1
        while i < len(lines):
            n2, indent2, content2 = lines[i]
            if indent2 <= seq_indent:
                break
            split2 = _split_key(content2)
            if split2 is None:
                raise MiniYamlError("line %d: not a mapping entry: %r" % (n2, content2))
            k2, v2 = split2
            if k2 in entry:
                raise MiniYamlError("line %d: duplicate key %r" % (n2, k2))
            if not v2:
                raise MiniYamlError("line %d: nested structures are not accepted" % n2)
            entry[k2] = [] if v2 == "[]" else _scalar(v2)
            i += 1
        items.append(entry)
    if not items:
        raise MiniYamlError("empty block sequence")
    return items, i
