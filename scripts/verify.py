#!/usr/bin/env python3
"""Record repeatable acceptance commands; never invoke a model."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--with-codex', action='store_true')
    args = parser.parse_args()
    reports = ROOT / 'reports'
    reports.mkdir(exist_ok=True)
    record_path = reports / 'verification.json'
    previous = json.loads(record_path.read_text()) if record_path.exists() else {}
    commands = [
        ['scripts/course.py', 'check'],
        ['examples/taskboard/acceptance.py'],
        ['scripts/course.py', 'lab', 'loop'],
        ['scripts/course.py', 'lab', 'loop', '--fail-tool'],
        ['scripts/course.py', 'lab', 'loop', '--max-tool-calls', '0'],
        ['scripts/course.py', 'lab', 'instructions'],
        ['scripts/course.py', 'lab', 'policy', '--isolation', 'read-only', '--approved'],
        ['scripts/course.py', 'lab', 'context'],
        ['scripts/course.py', 'lab', 'subagents'],
        ['scripts/course.py', 'lab', 'mcp-demo'],
    ]
    if args.with_codex:
        commands += [['scripts/course.py', 'lab', 'probe'], ['scripts/course.py', 'lab', 'app-server']]
    record = {
        'recorded_at': datetime.now(timezone.utc).isoformat(),
        'environment': {'python': platform.python_version(), 'system': platform.system(), 'release': platform.release(), 'machine': platform.machine()},
        'upstream': json.loads((ROOT / 'references/upstream.json').read_text())['commit'],
        'commands': [],
        'browser': previous.get('browser', {'status': 'not_run'}),
        'real_model': previous.get('real_model', {'status': 'not_run', 'note': 'This script never calls a model.'}),
        'independent_checks': previous.get('independent_checks', []),
        'codex_integration_selected': args.with_codex,
    }
    # These files exist before build so acceptance links are valid on a clean checkout.
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    log_path = reports / 'checks.log'
    with log_path.open('w') as log:
        for arguments in commands:
            start = time.monotonic()
            result = subprocess.run([sys.executable, *arguments], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90)
            output = result.stdout.replace(str(ROOT), '<REPO>')
            command = 'python3 ' + ' '.join(arguments)
            log.write(f'$ {command}\n{output}\n[exit {result.returncode}]\n\n')
            log.flush()
            record['commands'].append({'command': command, 'exit_code': result.returncode, 'elapsed_seconds': round(time.monotonic() - start, 3), 'output': output})
            print(f'{"PASS" if result.returncode == 0 else "FAIL"} {command}', flush=True)
    log_path.write_text(log_path.read_text().rstrip() + '\n')
    record['all_selected_commands_passed'] = all(c['exit_code'] == 0 for c in record['commands'])
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    # Export the completed record to the static site, not the earlier partial copy.
    result = subprocess.run([sys.executable, 'scripts/course.py', 'build'], cwd=ROOT)
    return 0 if record['all_selected_commands_passed'] and result.returncode == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
