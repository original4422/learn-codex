#!/usr/bin/env python3
"""Copy a runnable baseline into a new practice directory; never overwrite it."""

import argparse
from pathlib import Path
import shutil


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args(argv)
    destination = args.destination.resolve()
    if destination.exists():
        parser.exit(2, "destination already exists; choose a new directory to preserve your work\n")
    destination.mkdir(parents=True)
    source = Path(__file__).resolve().parent
    shutil.copy2(source / "starter.py", destination / "taskboard.py")
    (destination / "AGENTS.md").write_text(
        "# Taskboard practice\n\n"
        "Keep the CLI's add/list/done behavior compatible. Use only the Python standard library.\n"
        "Keep IDs deterministic, preserve invalid input files, and use atomic saves.\n"
        "Add exact, normalized tag matching without substring matches.\n"
        "Run the supplied acceptance script from the course repository after changes.\n\n"
        "保留 add/list/done 行为；只用 Python 标准库。ID 确定、损坏文件不覆盖、原子保存。\n"
        "标签应先去除首尾空白并转小写，再做精确匹配。修改后运行课程验收脚本。\n",
        encoding="utf-8")
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
