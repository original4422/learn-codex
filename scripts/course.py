#!/usr/bin/env python3
"""One entry point. Offline commands never require a Codex login."""
from __future__ import annotations
import argparse
import functools
import http.server
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build", help="Build the bilingual static site")
    sub.add_parser("check", help="Test labs, build and validate all local links")
    sub.add_parser("test", help="Run offline behavior tests")
    serve = sub.add_parser("serve", help="Build and preview on loopback only")
    serve.add_argument("--port", type=int, default=8765)
    lab = sub.add_parser("lab", help="Run a lab; append --help for lab commands")
    lab.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    os.chdir(ROOT)
    # All generated caches and temporary fixtures stay in this repository.
    (ROOT / ".cache/tmp").mkdir(parents=True, exist_ok=True)
    os.environ["TMPDIR"] = str(ROOT / ".cache/tmp")
    import tempfile
    tempfile.tempdir = os.environ["TMPDIR"]
    if args.command == "lab":
        from codex_lab.__main__ import main as run_lab
        return run_lab(args.arguments)
    if args.command in ("test", "check"):
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
        completed = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], env=env)
        if completed.returncode:
            return completed.returncode
        if args.command == "check":
            skill_check = subprocess.run([sys.executable, "examples/taskboard/.agents/skills/taskboard-check/scripts/check.py"], env=env)
            if skill_check.returncode:
                return skill_check.returncode
    if args.command in ("build", "check", "serve"):
        from build_site import build, validate
        build()
        validate()
    if args.command == "serve":
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT / "dist"))
        with http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
            print(f"learn-codex → http://127.0.0.1:{args.port} (Ctrl-C to stop)", flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
