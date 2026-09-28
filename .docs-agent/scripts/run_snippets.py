"""Run every code sample on the pages a PR changed, against the staging workspace.

  python run_snippets.py --base origin/main  → run/snippets.json

What it does
  1. Finds .mdx/.md files changed vs --base.
  2. Extracts fenced code blocks tagged bash/shell/curl, js/javascript/ts/node,
     python/py. Blocks whose info string contains `norun` are skipped
     (e.g. ```python norun). Response examples (```json) are collected, not run,
     so the reviewer can compare them with real responses.
  3. Replaces documented placeholders with staging credentials/test fixtures
     (see PLACEHOLDERS). Unknown placeholders are reported, not guessed.
  4. Runs each block with a timeout and records exit code, stdout, stderr.

The reviewer agent reads run/snippets.json and decides pass/fail. This script
never judges; it only executes and records.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from common import ROOT, RUN_DIR, config

STAGING = config()["reviewer"]["staging"]

# Placeholder used in docs → value used in the test run.
_K = os.environ.get("SUPRSEND_STAGING_WORKSPACE_KEY", "")
_S = os.environ.get("SUPRSEND_STAGING_WORKSPACE_SECRET", "")
_A = os.environ.get("SUPRSEND_STAGING_API_KEY", "")
_T = os.environ.get("SUPRSEND_STAGING_SERVICE_TOKEN", "")
# Keys are matched case-insensitively. Longest first, so __YOUR_API_KEY__ isn't
# half-replaced by YOUR_API_KEY.
PLACEHOLDERS = {
    # Credentials, in every spelling found on docs.suprsend.com
    "_workspace_key_": _K, "__workspace_key__": _K, "YOUR_WORKSPACE_KEY": _K, "__YOUR_WORKSPACE_KEY__": _K,
    "_workspace_secret_": _S, "__workspace_secret__": _S, "YOUR_WORKSPACE_SECRET": _S, "__YOUR_WORKSPACE_SECRET__": _S,
    "__YOUR_API_KEY__": _A, "YOUR_API_KEY": _A, "<API_KEY>": _A, "_API_key_": _A, "_APIKey_": _A,
    "__API_KEY__": _A, "_api_key_": _A,
    "<SERVICE_TOKEN>": _T, "YOUR_SERVICE_TOKEN": _T, "__SERVICE_TOKEN__": _T, "_service_token_": _T,
    # IDs that must exist in the staging workspace
    "_workflow_slug_": STAGING["test_workflow_slug"], "__workflow_slug__": STAGING["test_workflow_slug"],
    "_distinct_id_": STAGING["test_user_distinct_id"], "__distinct_id__": STAGING["test_user_distinct_id"],
    "_tenant_id_": STAGING["test_tenant_id"], "__tenant_id__": STAGING["test_tenant_id"],
}
FIXTURES = {
    "distinct_id": STAGING["test_user_distinct_id"],
    "workflow": STAGING["test_workflow_slug"],
    "tenant_id": STAGING["test_tenant_id"],
}
LANGS = {
    "bash": "bash", "sh": "bash", "shell": "bash", "curl": "bash",
    "js": "node", "javascript": "node", "node": "node", "ts": "node", "typescript": "node",
    "python": "python", "py": "python",
}
# Fences may be indented (inside <Steps>, <Tab>, lists); the indent is removed before running.
FENCE = re.compile(r"^([ \t]*)```([^\n]*)\n(.*?)^[ \t]*```", re.M | re.S)
PLACEHOLDER_HINT = re.compile(r"(__[A-Za-z_]+__|\b_[A-Za-z]+(?:_[A-Za-z]+)*_\b|\bYOUR_[A-Z_]+|<[A-Za-z_\-]{3,}>)")


def changed_files(base: str) -> list[Path]:
    out = subprocess.run(["git", "diff", "--name-only", f"{base}...HEAD"],
                         capture_output=True, text=True, cwd=ROOT, check=True).stdout
    return [ROOT / p for p in out.split() if p.endswith((".mdx", ".md"))
            and not p.startswith(".docs-agent/") and not p.startswith(".claude/")
            and (ROOT / p).exists()]


def substitute(code: str) -> tuple[str, list[str]]:
    # Longest first, so __YOUR_WORKSPACE_KEY__ isn't half-replaced by YOUR_WORKSPACE_KEY.
    for k, v in sorted(PLACEHOLDERS.items(), key=lambda kv: -len(kv[0])):
        if v:
            code = re.sub(re.escape(k), lambda _m: v, code, flags=re.I)
    known = {k.lower() for k in PLACEHOLDERS}
    unknown = sorted({p for p in PLACEHOLDER_HINT.findall(code) if p.lower() not in known})
    return code, unknown


TESTER = ROOT / ".docs-agent" / "tester"


def run_block(runtime: str, lang: str, code: str, timeout: int = 60) -> dict:
    """Snippets are written inside tester/ so both CommonJS require() and ESM import
    resolve the SDKs from tester/node_modules (ESM ignores NODE_PATH)."""
    env = {**os.environ, "SUPRSEND_API_BASE": STAGING["api_base"]}
    with tempfile.TemporaryDirectory(dir=TESTER, prefix=".snippet-") as d:
        if runtime == "node":
            is_ts = lang in ("ts", "typescript")
            esm = bool(re.search(r"^\s*import\s", code, re.M))
            ext = (".mts" if esm else ".cts") if is_ts else (".mjs" if esm else ".cjs")
            f = Path(d) / f"snippet{ext}"
            cmd = [str(TESTER / "node_modules" / ".bin" / "tsx"), str(f)] if is_ts \
                else ["node", str(f)]
        elif runtime == "python":
            f = Path(d) / "snippet.py"
            cmd = ["python3", str(f)]
        else:
            f = Path(d) / "snippet.sh"
            cmd = ["bash", "-euo", "pipefail", str(f)]
        f.write_text(code)
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                               env=env, cwd=TESTER)
            return {"exit_code": p.returncode, "stdout": p.stdout[-6000:],
                    "stderr": p.stderr[-6000:]}
        except subprocess.TimeoutExpired:
            return {"exit_code": None, "stdout": "", "stderr": f"timeout after {timeout}s"}
        except FileNotFoundError as e:
            return {"exit_code": None, "stdout": "", "stderr": f"runner missing: {e}"}


def scrub(text: str) -> str:
    for v in (_K, _S, _A, _T):          # credentials only; fixture IDs stay readable
        if v:
            text = text.replace(v, "[staging-secret]")
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main")
    args = ap.parse_args()

    results = []
    for path in changed_files(args.base):
        text = path.read_text()
        for i, m in enumerate(FENCE.finditer(text)):
            indent, info, code = m.group(1), m.group(2).strip(), m.group(3)
            if indent:
                code = "\n".join(l[len(indent):] if l.startswith(indent) else l.lstrip()
                                  for l in code.split("\n"))
            tag = (info.split() or [""])[0].lower()
            line = text[: m.start()].count("\n") + 1
            rec = {"file": str(path.relative_to(ROOT)), "line": line, "lang": tag, "info": info}
            if tag == "json":
                rec.update(kind="expected_output", code=code[:4000])
            elif tag not in LANGS:
                continue
            elif "norun" in info:
                rec.update(kind="skipped", reason="marked norun")
            else:
                code2, unknown = substitute(code)
                rec.update(kind="executed", unknown_placeholders=unknown, fixtures=FIXTURES,
                           **run_block(LANGS[tag], tag, code2))
                rec["stdout"], rec["stderr"] = scrub(rec["stdout"]), scrub(rec["stderr"])
                rec["code"] = code[:4000]
            results.append(rec)

    out = RUN_DIR / "snippets.json"
    out.write_text(json.dumps(results, indent=2))
    ran = [r for r in results if r["kind"] == "executed"]
    failed = [r for r in ran if r["exit_code"] != 0]
    print(f"snippets: {len(ran)} run, {len(failed)} non-zero exit → {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
