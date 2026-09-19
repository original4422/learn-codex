"""Uniform entry point: python3 -m codex_lab COMMAND."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

from . import adapters, mechanisms, mcp_server


def main(argv=None):
    parser = argparse.ArgumentParser(description="Learn Codex: explicit teaching models and real protocol experiments")
    commands = parser.add_subparsers(dest="command", required=True)
    loop = commands.add_parser("loop", help="deterministic mock agent loop")
    loop.add_argument("--max-steps", type=int, default=4)
    loop.add_argument("--max-tool-calls", type=int, default=2)
    loop.add_argument("--fail-tool", action="store_true")
    instructions = commands.add_parser("instructions", help="explicit-root instruction discovery model")
    instructions.add_argument("--root", type=Path, default=adapters.ROOT / "examples/instructions/repo")
    instructions.add_argument("--cwd", type=Path, default=adapters.ROOT / "examples/instructions/repo/app")
    instructions.add_argument("--home", type=Path, default=adapters.ROOT / "examples/instructions/home")
    instructions.add_argument("--max-bytes", type=int, default=2048)
    policy = commands.add_parser("policy", help="decision simulation; never executes an action")
    policy.add_argument("--approval", choices=["ask", "never"], default="ask")
    policy.add_argument("--isolation", choices=["read-only", "workspace-write"], default="read-only")
    policy.add_argument("--action", choices=["read", "write", "network"], default="write")
    policy.add_argument("--approved", action="store_true")
    for name in ("context", "subagents", "mcp-demo", "probe"):
        commands.add_parser(name)
    mcp = commands.add_parser("mcp-server", help="real bounded MCP stdio server")
    mcp.add_argument("--root", type=Path, default=adapters.ROOT / "examples/mcp-data")
    app = commands.add_parser("app-server", help="real no-model Codex App Server handshake")
    app.add_argument("--timeout", type=float, default=15)
    execute = commands.add_parser("exec", help="real Codex model run; requires explicit --allow-model")
    execute.add_argument("--allow-model", action="store_true")
    execute.add_argument("--model")
    execute.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args(argv)
    try:
        if args.command == "loop":
            result = mechanisms.run_loop(max_steps=args.max_steps, max_tool_calls=args.max_tool_calls, fail_tool=args.fail_tool)
        elif args.command == "instructions":
            result = mechanisms.discover_instructions(args.root, args.cwd, args.home, args.max_bytes)
        elif args.command == "policy":
            result = mechanisms.evaluate_policy(args.action, args.approval, args.isolation, args.approved)
        elif args.command == "context":
            result = mechanisms.context_demo()
        elif args.command == "subagents":
            result = mechanisms.subagent_demo()
        elif args.command == "mcp-server":
            mcp_server.serve(args.root)
            return 0
        elif args.command == "mcp-demo":
            result = adapters.mcp_demo()
        elif args.command == "probe":
            result = adapters.probe()
        elif args.command == "app-server":
            result = adapters.app_server_handshake(args.timeout)
        else:
            result = adapters.exec_summary(allow_model=args.allow_model, model=args.model, timeout=args.timeout)
    except (ValueError, OSError, RuntimeError, TimeoutError, subprocess.SubprocessError) as error:
        print(json.dumps({"status": "failed", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
