# Taskboard real coding exercise / 真实编程练习

Date / 日期: 2026-09-30. Teaching experiment / 教学实验.

## Protocol / 协议

One fresh starter, one bounded `codex exec` task, six external acceptance checks. / 一个新 starter、一次有界 `codex exec` 任务、六项外部验收。

```sh
python3 scripts/course.py lab exercise --allow-model --codex-home "$HOME/.codex" --model gpt-6-sol --timeout 240
```

The task requires normalized, sorted, deduplicated exact tags; legacy records; IDs; preserved invalid stores; and inclusive tag limits. The reference implementation and evaluator stay outside the candidate directory. Native Codex sandbox permissions deny reads of the course checkout and user home, with a specific candidate-directory write grant. The parent evaluates subprocess JSON and exit codes; the candidate never returns its own final verdict. / 任务要求标签归一化、排序、去重、精确过滤、旧数据兼容、ID 与损坏数据保全及标签边界。答案和验收器留在候选工作区外；原生 Codex 沙箱禁止读取课程目录和用户 home，仅放行候选目录。父进程根据 CLI JSON 和退出码独立判定。

The course home was not authenticated. An explicitly selected existing ChatGPT login is used without copying credentials or changing configuration. The run uses `--ignore-user-config`, `--ignore-rules`, `--ephemeral`, no web search and no subagents. / 课程 home 未登录；显式选择已有 ChatGPT 登录，不复制凭据、不改配置。忽略用户配置和规则、使用临时会话、禁用网页搜索和子 Agent。

Source baseline / 源码基线: [exec flags](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/exec/src/cli.rs), [named permissions](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/config/src/permissions_toml.rs).

## Offline controls / 离线对照

- Copied reference: all six pass. / 参考实现副本：六项通过。
- Unmodified starter: rejected. / 未修改 starter：拒绝。
- Substring matching mutation: exact-match check fails. / 子串匹配错误版：精确匹配检查失败。
- Missing 40-character limit: invalid-tag check fails. / 删除 40 字符限制：非法标签检查失败。
- Actual sandbox probe: candidate read/write allowed; answer, oracle and login directory return PermissionError. / 真实沙箱探针：候选可读写，答案、验收器与登录目录均不可读。
- Copied reference under the same native sandbox: 6/6. / 相同原生沙箱中的参考实现副本：6/6。

## Model result / 模型结果

One real attempt passed all 6 checks. No repair attempt or additional sampling. / 一次真实尝试通过全部六项检查，没有补救任务或追加采样。

| Observation / 观察 | Value / 数值 |
| --- | --- |
| CLI / model / effort | 0.155.1 / gpt-6-sol / low |
| Host / Python | macOS 15.7.8 / Python 3.14.7 |
| Total elapsed / 总耗时 | 61.958 s |
| Model stage / 模型阶段 | 60.725 s |
| Completed tool events / 已完成工具事件 | 8 |
| Input tokens / 输入 | 161563 |
| Cached input tokens, subset / 缓存输入，输入子集 | 123904 |
| Output tokens / 输出 | 2008 |
| External acceptance / 外部验收 | 6/6 |
| Starter, reference, evaluator / 原 starter、答案与验收器 | SHA-256 unchanged / 未变 |

The first three shell commands failed with exit 127 because `inherit=none` removed PATH. The model recovered using absolute `/bin/cat` and `/usr/bin/python3`, edited the actual starter, and ran its own CLI checks within the same attempt. These failures remain in the private events. / 最初三条 shell 命令因 PATH 被清除而以127失败；模型在同一任务中改用绝对路径，自主完成读代码、修改和自检，首败保留在私有事件中。

After the measured attempt, the launcher was corrected to explicitly set a minimal PATH/HOME/TMPDIR. A no-model native sandbox shell check confirmed `python3`, `cat` and `sed` resolve. The published launcher includes this fix; the table above describes the original attempt, including its recovery. / 测量后入口补上最小 PATH/HOME/TMPDIR；无模型原生沙箱 shell 验证三个命令可用。发布代码包含此修复，上表仍记录包含自主恢复的原始尝试。

See [aggregate result with six verdicts and hashes](taskboard-exercise-result.json) and [the actual candidate diff](taskboard-exercise.diff). The independent evaluator, not the final model message, supplies the pass result. / 参见六项判定与 hash 汇总和实际候选 diff；通过结论来自外部验收器。

## Reproduction artifacts / 复现产物

Each attempt stores private `phases.jsonl`, `events.jsonl`, `stderr.log`, `last-message.txt`, `candidate.diff` and `result.json` beneath ignored `.cache/exercises/`. Failures are kept separately and never overwritten by a later attempt. Public reports contain only task-specific aggregate facts and hashes. / 每次运行在忽略的 `.cache/exercises/` 中保存独立的阶段、事件、诊断、最终消息、diff 和结果；后续尝试不会覆盖首败。公开记录只包含任务统计和 hash。
