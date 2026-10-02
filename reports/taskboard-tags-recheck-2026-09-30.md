# Taskboard tag-preservation recheck / 标签保留重验

Date / 日期: 2026-09-30 (Asia/Shanghai). No model calls / 未调用模型。

Independent review found a missing assertion in the external evaluator: `done` must preserve tags, but the original check only queried open tasks after completion. Adding `task["tags"] = []` to the reference implementation's `done` branch still passed all six checks. / 独立复核发现外部验收器缺少断言：任务要求 `done` 保留标签，原检查却仅查询完成后的未完成任务。向参考实现的 `done` 分支加入 `task["tags"] = []`，仍能通过全部六项检查。

The same second check now asserts the tags returned by `done`, then checks both the ID and stored tags returned by `list --tag study --status done`. The evaluator retains its six-check structure. A new mutation test failed against the old evaluator and passed after these assertions were added; the unchanged reference still passes 6/6. / 现在第二项检查同时断言 `done` 返回的标签，以及 `list --tag study --status done` 返回的 ID 和持久化标签。仍保留六项检查结构。新增错误版测试在旧验收器下失败，补充断言后通过；未修改的参考实现仍为 6/6。

The archived real model candidate was copied to a fresh temporary workspace and rechecked using the strengthened evaluator and the same native Codex sandbox permission scheme. The actual isolation probe passed, and all six checks passed. The candidate hash remained unchanged. / 已保存的真实模型候选复制到新的临时工作区，使用增强后的验收器和相同的原生 Codex 沙箱权限方案重验。真实隔离探针通过，六项检查全部通过，候选 hash 未变。

The [original model report](taskboard-live-exercise-2026-09-30.md), [original result](taskboard-exercise-result.json), and measured timing/usage remain unchanged. This is a separate no-model correctness recheck. The [recheck JSON](taskboard-tags-recheck-2026-09-30.json) links the original result hash, original and strengthened evaluator hashes, candidate hash, sandbox observation and six verdicts. / [原模型报告](taskboard-live-exercise-2026-09-30.md)、[原结果](taskboard-exercise-result.json)及其耗时、usage 均保持原样。本记录是独立的无模型正确性重验；[重验 JSON](taskboard-tags-recheck-2026-09-30.json)关联原结果 hash、新旧验收器 hash、候选 hash、沙箱观察和六项判定。

Reproduce the offline mutation control / 复现离线错误版对照：

```sh
PYTHONPATH=src:tests python3 -m unittest test_live_exercise.ExerciseTests.test_done_clearing_tags_rejected
```
