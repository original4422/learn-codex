"""Deterministic teaching models. None implements Codex's native machinery."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

SAMPLE_TASKS = [
    {"id": 1, "title": "Read code", "done": True, "tags": ["study"]},
    {"id": 2, "title": "Add filter", "done": False, "tags": ["feature", "study"]},
    {"id": 3, "title": "Test failure", "done": False, "tags": ["test"]},
]


@dataclass(frozen=True)
class Action:
    kind: str
    name: str = ""
    arguments: dict | None = None
    text: str = ""


class MockPlanner:
    """A scripted policy: test the loop plumbing, not model intelligence."""

    def next_action(self, observations):
        if not observations:
            return Action("tool", "list_tasks", {"status": "open"})
        if not observations[-1]["ok"]:
            return Action("final", text="Could not inspect tasks; report the tool failure.")
        return Action("final", text=f"{len(observations[-1]['value'])} open tasks remain.")


def run_loop(planner=None, *, max_steps=4, max_tool_calls=2, fail_tool=False):
    if max_steps < 1 or max_tool_calls < 0:
        raise ValueError("max_steps must be positive; max_tool_calls must be nonnegative")
    planner = planner or MockPlanner()
    observations, events = [], []
    calls = 0
    for step in range(max_steps):
        action = planner.next_action(deepcopy(observations))
        if not isinstance(action, Action):
            raise ValueError("planner must return an Action")
        if action.kind == "final":
            events.append({"type": "final", "step": step, "text": action.text})
            return {"implementation": "teaching mock", "status": "completed", "events": events}
        if action.kind != "tool":
            raise ValueError("unknown action kind")
        if calls >= max_tool_calls:
            events.append({"type": "budget.exhausted", "budget": "tool_calls"})
            break
        calls += 1
        events.append({"type": "tool.started", "step": step, "tool": action.name})
        try:
            if action.name != "list_tasks":
                raise ValueError("tool is not registered")
            if action.arguments not in ({"status": "open"}, {"status": "all"}):
                raise ValueError("invalid list_tasks arguments")
            if fail_tool:
                raise OSError("simulated read failure")
            value = [deepcopy(t) for t in SAMPLE_TASKS
                     if action.arguments["status"] == "all" or not t["done"]]
            observation = {"ok": True, "value": value}
        except (OSError, ValueError) as error:
            observation = {"ok": False, "error": str(error)}
        observations.append(observation)
        events.append({"type": "tool.completed", "step": step, **observation})
    else:
        events.append({"type": "budget.exhausted", "budget": "steps"})
    return {"implementation": "teaching mock", "status": "budget_exhausted", "events": events}


def discover_instructions(root, cwd, home=None, max_bytes=2048):
    """Explicit root→cwd model; no Git discovery, trust UI, or config parsing."""
    root, cwd = Path(root).resolve(), Path(cwd).resolve()
    if not root.is_dir() or not cwd.is_dir() or not cwd.is_relative_to(root):
        raise ValueError("cwd must be an existing directory inside root")
    if max_bytes < 1:
        raise ValueError("max_bytes must be positive")
    directories = [root]
    relative = cwd.relative_to(root)
    for part in relative.parts:
        directories.append(directories[-1] / part)
    if home is not None:
        directories.insert(0, Path(home).resolve())
    selected, total = [], 0
    for directory_index, directory in enumerate(directories):
        for name in ("AGENTS.override.md", "AGENTS.md"):
            path = directory / name
            if not path.is_file():
                continue
            with path.open("rb") as handle:
                raw = handle.read(max_bytes + 1)
            if not raw.strip():
                # Global discovery skips empty files; project discovery selects
                # the first existing file, so an empty override shadows AGENTS.
                if home is not None and directory_index == 0:
                    continue
                break
            remaining = max_bytes - total
            data = raw[:remaining]
            text = data.decode("utf-8", errors="ignore")
            used = len(text.encode("utf-8"))
            selected.append({"path": str(path), "text": text,
                             "bytes": used, "truncated": len(raw) > used})
            total += used
            break
        if total >= max_bytes or (selected and selected[-1]["truncated"]):
            break
    return {"implementation": "teaching simplification", "files": selected, "bytes": total,
            "note": "Ordered text composition, not an instruction-conflict resolver."}


def evaluate_policy(action, approval="ask", isolation="read-only", approved=False):
    """Two independent decisions; deliberately never runs a command."""
    if action not in {"read", "write", "network"}:
        raise ValueError("unknown action")
    if approval not in {"ask", "never"} or isolation not in {"read-only", "workspace-write"}:
        raise ValueError("unknown policy")
    needs_approval = action != "read"
    consent = not needs_approval or (approval == "ask" and approved)
    within_boundary = action == "read" or (action == "write" and isolation == "workspace-write")
    return {"implementation": "teaching simulation; no OS sandbox installed",
            "action": action, "approval_satisfied": consent, "isolation_allows": within_boundary,
            "would_execute": consent and within_boundary,
            "note": "Approval alone does not change the execution boundary. These rules are illustrative, not Codex policy."}


def compact_context(messages, *, keep_last=2, max_chars=700):
    """Structured extractive memory, not Codex's model-driven summarizer."""
    if keep_last < 0 or max_chars < 1:
        raise ValueError("invalid compaction limits")
    allowed = {"constraint", "decision", "open", "message", "tool"}
    if any(not isinstance(m, dict) or m.get("kind") not in allowed or
           not isinstance(m.get("text"), str) for m in messages):
        raise ValueError("messages need kind and text")
    pinned = [deepcopy(m) for m in messages if m["kind"] in {"constraint", "decision", "open"}]
    cost = sum(len(m["text"]) for m in pinned)
    if cost > max_chars:
        raise ValueError("protected facts exceed budget: revise scope instead of silently dropping them")
    tail = [deepcopy(m) for m in messages if m["kind"] not in {"constraint", "decision", "open"}]
    tail = tail[-keep_last:] if keep_last else []
    while tail and cost + sum(len(m["text"]) for m in tail) > max_chars:
        tail.pop(0)
    result = pinned + tail
    return {"implementation": "teaching extractive compactor; characters, not tokens",
            "before_chars": sum(len(m["text"]) for m in messages),
            "after_chars": sum(len(m["text"]) for m in result), "memory": result,
            "dropped_messages": len(messages) - len(result)}


def context_demo():
    return compact_context([
        {"kind": "constraint", "text": "Keep IDs deterministic. Never overwrite invalid JSON."},
        {"kind": "tool", "text": "verbose successful test output " * 70},
        {"kind": "decision", "text": "Tags use exact normalized matching."},
        {"kind": "open", "text": "Need a regression test for replace failure."},
        {"kind": "message", "text": "Next: inspect tests/test_taskboard.py."},
    ], keep_last=1)


def audit_worker(scope, tasks):
    """Independent deterministic reviewers; no LLM and no child Codex process."""
    if scope == "open-work":
        ids = [t["id"] for t in tasks if not t["done"]]
    elif scope == "coverage":
        ids = [t["id"] for t in tasks if "test" in t["tags"]]
    else:
        raise ValueError("unknown audit scope")
    return {"scope": scope, "task_ids": ids, "evidence": "snapshot predicates"}


def aggregate_reviews(reports, tasks):
    known = {t["id"] for t in tasks}
    seen = set()
    for report in reports:
        if not isinstance(report, dict) or set(report) != {"scope", "task_ids", "evidence"}:
            raise ValueError("invalid review schema")
        if report["scope"] in seen or report["scope"] not in {"open-work", "coverage"}:
            raise ValueError("duplicate or unknown scope")
        seen.add(report["scope"])
        if not isinstance(report["task_ids"], list) or any(type(i) is not int or i not in known for i in report["task_ids"]):
            raise ValueError("review cites an unknown task")
        expected = audit_worker(report["scope"], tasks)["task_ids"]
        if report["task_ids"] != expected:
            raise ValueError("review evidence does not match the source snapshot")
    if seen != {"open-work", "coverage"}:
        raise ValueError("both review scopes are required")
    return sorted(reports, key=lambda r: r["scope"])


def subagent_demo():
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(audit_worker, scope, deepcopy(SAMPLE_TASKS))
                   for scope in ("open-work", "coverage")]
        reports = [future.result(timeout=5) for future in futures]
    return {"implementation": "teaching simulation using independent Python workers; no Codex agents",
            "reports": aggregate_reviews(reports, SAMPLE_TASKS), "verified_against_snapshot": True}
