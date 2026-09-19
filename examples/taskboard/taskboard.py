#!/usr/bin/env python3
"""Taskboard: a deliberately small, single-writer JSON task CLI.

Run from the repository root. Atomic replace prevents partial files; it does
not implement a transaction across concurrent readers and writers.
"""

import argparse
import json
import os
from pathlib import Path
import tempfile

MAX_BYTES = 1_000_000
MAX_TASKS = 10_000


def normalize_tags(tags):
    if not isinstance(tags, list) or any(not isinstance(t, str) for t in tags):
        raise ValueError("tags must be a list of strings")
    result = sorted(set(t.strip().lower() for t in tags))
    if len(result) > 20 or any(not t or len(t) > 40 for t in result):
        raise ValueError("provide at most 20 nonempty tags, each at most 40 characters")
    return result


def validate(data):
    if not isinstance(data, list) or len(data) > MAX_TASKS:
        raise ValueError("store must be a JSON array with at most 10000 tasks")
    ids = set()
    for task in data:
        if not isinstance(task, dict) or set(task) not in (
            {"id", "title", "done"}, {"id", "title", "done", "tags"}
        ):
            raise ValueError("invalid task fields")
        if type(task["id"]) is not int or task["id"] < 1 or task["id"] in ids:
            raise ValueError("task IDs must be distinct positive integers")
        if not isinstance(task["title"], str) or not task["title"].strip() or len(task["title"]) > 200:
            raise ValueError("task titles must contain 1–200 characters")
        if type(task["done"]) is not bool:
            raise ValueError("task done must be a boolean")
        ids.add(task["id"])
        task["tags"] = normalize_tags(task.get("tags", []))
    return data


def load(store):
    store = Path(store)
    if not store.exists():
        return []
    if not store.is_file():
        raise ValueError("store must be a regular file")
    with store.open("rb") as handle:
        raw = handle.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("store exceeds 1000000 bytes")
    try:
        data = json.loads(raw.decode("utf-8"))
    except RecursionError as error:
        raise ValueError("store JSON nesting is too deep") from error
    return validate(data)


def save(store, tasks):
    """Write in the destination directory, fsync, then atomically replace."""
    store = Path(store)
    validate(tasks)
    payload = (json.dumps(tasks, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if len(payload) > MAX_BYTES:
        raise ValueError("store exceeds 1000000 bytes")
    store.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=store.parent, prefix=".taskboard-", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, store)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def add(store, title, tags=None):
    title = title.strip()
    if not title or len(title) > 200:
        raise ValueError("title must contain 1–200 characters")
    tasks = load(store)
    task = {"id": max((t["id"] for t in tasks), default=0) + 1,
            "title": title, "done": False, "tags": normalize_tags(tags or [])}
    tasks.append(task)
    save(store, tasks)
    return task


def list_tasks(store, tag=None, status="all"):
    if status not in {"all", "open", "done"}:
        raise ValueError("status must be all, open, or done")
    if tag is not None:
        tag = normalize_tags([tag])[0]
    return [t for t in load(store)
            if (tag is None or tag in t["tags"])
            and (status == "all" or t["done"] == (status == "done"))]


def done(store, task_id):
    tasks = load(store)
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            save(store, tasks)
            return task
    raise ValueError(f"task {task_id} does not exist")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, default=Path(".local/taskboard.json"))
    commands = parser.add_subparsers(dest="command", required=True)
    add_parser = commands.add_parser("add")
    add_parser.add_argument("title")
    add_parser.add_argument("--tag", action="append", default=[])
    list_parser = commands.add_parser("list")
    list_parser.add_argument("--tag")
    list_parser.add_argument("--status", choices=["all", "open", "done"], default="all")
    commands.add_parser("done").add_argument("id", type=int)
    args = parser.parse_args(argv)
    try:
        if args.command == "add":
            result = add(args.store, args.title, args.tag)
        elif args.command == "list":
            result = list_tasks(args.store, args.tag, args.status)
        else:
            result = done(args.store, args.id)
    except (ValueError, OSError) as error:
        parser.exit(2, f"taskboard: {error}\n")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
