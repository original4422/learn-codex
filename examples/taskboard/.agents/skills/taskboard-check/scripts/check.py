#!/usr/bin/env python3
"""Bounded black-box smoke check, independent of Codex/model availability."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def check(target):
    target = Path(target).resolve()
    if not target.is_file():
        raise ValueError(f"target does not exist: {target}")
    passed = []
    temporary_root = target.parent / ".local"
    temporary_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="taskboard-skill-", dir=temporary_root) as directory:
        store = Path(directory) / "tasks.json"

        def invoke(*args, expected=0):
            result = subprocess.run(
                [sys.executable, str(target), "--store", str(store), *args],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != expected:
                raise ValueError(f"{args[0]} exited {result.returncode}, expected {expected}: {result.stderr.strip()}")
            if expected:
                if result.stdout.strip():
                    raise ValueError("rejected command must not print success JSON")
                return None
            try:
                value = json.loads(result.stdout)
            except json.JSONDecodeError as error:
                raise ValueError(f"{args[0]} did not emit one JSON value") from error
            expected_type = list if args[0] == "list" else dict
            if not isinstance(value, expected_type):
                raise ValueError(f"{args[0]} emitted the wrong JSON shape")
            if isinstance(value, list) and any(not isinstance(item, dict) for item in value):
                raise ValueError("list must emit an array of task objects")
            return value

        task = invoke("add", "Check tags", "--tag", " Study ", "--tag", "study")
        if task.get("id") != 1 or task.get("tags") != ["study"] or task.get("done") is not False:
            raise ValueError("add did not normalize/deduplicate tags or initialize the task")
        passed.append("normalized_add")
        invoke("add", "Other task", "--tag", "studying")
        selected = invoke("list", "--tag", "STUDY")
        if [item["id"] for item in selected] != [1]:
            raise ValueError("tag filter must use normalized exact matching")
        passed.append("exact_tag_filter")
        task = invoke("done", "1")
        if task.get("done") is not True or task.get("tags") != ["study"]:
            raise ValueError("completion did not preserve tags")
        if invoke("list", "--tag", "study", "--status", "open") != []:
            raise ValueError("open-status filter included a completed task")
        passed.append("completion_and_status")
        before = store.read_bytes()
        invoke("add", " ", expected=2)
        if store.read_bytes() != before:
            raise ValueError("rejected input changed the existing store")
        passed.append("rejection_preserves_store")
    return {"check": "taskboard-skill-smoke", "status": "passed", "passed": passed,
            "scope": "real local subprocess behavior; no model invocation"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=Path(__file__).resolve().parents[4] / "taskboard.py")
    args = parser.parse_args()
    try:
        result = check(args.target)
    except (ValueError, OSError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"check": "taskboard-skill-smoke", "status": "failed", "error": str(error)}))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
