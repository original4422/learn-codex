#!/usr/bin/env python3
"""Trusted prefix and business checks for a locally edited teaching consumer."""

import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from codex_lab.adapters import validate_summary

HERE = Path(__file__).resolve().parent
ACTIONS = {"wait", "continue", "verify", "failed"}


def load_consumer(path):
    spec = importlib.util.spec_from_file_location("completion_candidate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.progress


def accept_answer(action, answer):
    """The host owns task correctness, separate from the student's event consumer."""
    if action != "verify":
        return False
    try:
        validate_summary(answer)
    except ValueError:
        return False
    return True


def check(progress, cases=None):
    cases = cases if cases is not None else json.loads((HERE / "cases.json").read_text())["cases"]
    checks = []
    for case in cases:
        events = []
        prefixes_ok = True
        action = None
        for prefix, step in enumerate([{"expected": "wait"}, *case["steps"]]):
            if "event" in step:
                events.append(step["event"])
            action = progress(copy.deepcopy(events), copy.deepcopy(case["context"]))
            passed = action in ACTIONS and action == step["expected"]
            prefixes_ok = prefixes_ok and passed
            checks.append({"case": case["name"], "prefix": prefix,
                           "expected": step["expected"], "actual": action, "passed": passed})
        for answer in case.get("answers", []):
            accepted = accept_answer(action, answer["value"]) if prefixes_ok else False
            checks.append({"case": case["name"], "answer": answer["name"],
                           "expected": answer["accepted"], "actual": accepted,
                           "passed": prefixes_ok and accepted == answer["accepted"]})
    failures = [c for c in checks if not c["passed"]]
    return {"verification": "offline fictional event prefixes + independent Taskboard summary check",
            "passed": not failures, "checks": len(checks), "first_failure": failures[0] if failures else None,
            "results": checks}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", type=Path, default=HERE / "reference.py")
    args = parser.parse_args(argv)
    result = check(load_consumer(args.script))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
