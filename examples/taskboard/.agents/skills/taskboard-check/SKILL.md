---
name: taskboard-check
description: Verify this course's Taskboard JSON CLI after changes to add, list, tags, or completion. Use for Taskboard acceptance checks, not general Python review or publishing.
---

# Taskboard behavioral check / Taskboard 行为检查

Use this workflow when the user requests Taskboard verification. This skill runs a local standard-library subprocess check with a temporary data store. It does not call a model, use the network, or publish anything.

用户要求验证 Taskboard 时使用本流程。脚本使用 Python 标准库、子进程和临时数据文件，不调用模型、不联网、不发布内容。

1. Resolve the Taskboard directory from this skill's own location: `.agents/skills/taskboard-check/` belongs to the directory containing `taskboard.py`. Read `taskboard.py` and relevant project instructions. 从 Skill 路径定位 Taskboard，先读实现与项目约定。
2. Run `python3 scripts/check.py` from this skill directory, or run the script by its absolute path from any directory. 若使用其他待验收实现，传入 `--target /absolute/path/taskboard.py`。The default target is the sibling example implementation, never an arbitrary working-directory file.
3. Read the exit status and JSON report. A nonzero exit is a failure to investigate, not permission to weaken assertions. 检查退出码与 JSON；失败时调查原因，不降低断言。
4. Report what passed, failed, and remains unverified. This is a focused black-box smoke check, not proof of full regression coverage or real-model skill selection. 报告覆盖范围：此脚本不是完整回归测试，也不能证明模型自动选择了 Skill。
5. If changes are needed, stay within the user's requested scope and rerun the check. Do not change production task stores or user configuration. 按用户授权范围修复并重跑，不改真实任务数据或用户配置。

Success means the subprocess interface preserves normalized tags, exact tag filtering, completion state, and stored bytes after rejected input. The script uses a fresh temporary directory and removes it when finished.
