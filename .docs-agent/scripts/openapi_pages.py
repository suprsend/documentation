"""Which reference pages does an openapi.yaml change affect?

  python openapi_pages.py origin/main     → prints reference/*.mdx paths, one per line

Compares openapi.yaml at <base> with the working tree. An operation counts as changed if
its own definition changed or if it references (directly or through other components) a
component schema that changed. Pages are matched through their `openapi: "METHOD /path"`
frontmatter.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "openapi.yaml"
REF = re.compile(r"#/components/(\w+)/([\w.\-]+)")


def load_base(base: str) -> dict:
    try:
        raw = subprocess.run(["git", "show", f"{base}:openapi.yaml"], capture_output=True,
                             text=True, check=True, cwd=ROOT).stdout
        return yaml.safe_load(raw) or {}
    except subprocess.CalledProcessError:
        return {}


def main(base: str):
    old, new = load_base(base), yaml.safe_load(SPEC.read_text()) or {}
    dump = lambda x: json.dumps(x, sort_keys=True, default=str)

    changed_comp = set()
    for kind, items in (new.get("components") or {}).items():
        for name, val in (items or {}).items():
            if dump(val) != dump(((old.get("components") or {}).get(kind) or {}).get(name)):
                changed_comp.add((kind, name))
    # propagate: a component that references a changed component is changed too
    comps = {(k, n): dump(v) for k, items in (new.get("components") or {}).items() for n, v in (items or {}).items()}
    grew = True
    while grew:
        grew = False
        for key, text in comps.items():
            if key not in changed_comp and any(ref in changed_comp for ref in REF.findall(text)):
                changed_comp.add(key)
                grew = True

    changed_ops = set()
    for path, ops in (new.get("paths") or {}).items():
        for method, op in (ops or {}).items():
            before = ((old.get("paths") or {}).get(path) or {}).get(method)
            text = dump(op)
            if dump(before) != text or any(ref in changed_comp for ref in REF.findall(text)):
                changed_ops.add((method.upper(), path.rstrip("/")))

    for page in sorted(ROOT.glob("reference/**/*.mdx")):
        m = re.search(r'^openapi:\s*["\']?(\w+)\s+(\S+?)["\']?\s*$', page.read_text(), re.M)
        if m and (m.group(1).upper(), m.group(2).rstrip("/")) in changed_ops:
            print(page.relative_to(ROOT))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "origin/main")
