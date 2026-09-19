# 09 · 子 Agent：拆分工作，也保留验证责任

## 学习目标

把 Taskboard 的两个独立审查问题并行委派，写清输入、范围与交付格式；理解上下文分叉不等于文件系统隔离；在汇总之前验证每份结论。产出是一份能指回代码或数据的合并审查结果。

## 先实际使用：委派可独立完成的问题

在 Taskboard 仓库的交互式 Codex 会话中发出下面的任务。这会请求真实模型工作，须有可用认证与模型；离线替代实验在后面。

```text
请使用两个子 Agent 并行审查 Taskboard，均只读，不修改文件。
A：检查 JSON 加载、校验和保存失败路径，最多给出三条有证据的风险。
B：检查标签归一化与筛选规则，列出已有测试和缺失边界情况。
各自返回：具体文件/函数、可复现输入、观察或推断、建议验证命令。
主 Agent：独立复核结果，去掉无证据项，合并重复项，运行必要测试。
不要把“子 Agent 说通过”作为测试通过的证据。
```

使用 `/agent` 查看或切换子任务，并在主任务中检查是否真的出现委派、子任务结果和汇总。当前官方文档说明子 Agent 可用于并行工作，且会产生各自的模型与工具用量；是否发生了委派，以本次轨迹为准。[官方使用说明](https://learn.chatgpt.com/docs/agent-configuration/subagents)

不要把两个工作都拆成“修改同一个保存函数”。只读探索容易并行；有依赖的修改先确定接口，再分配互不重叠的文件，最后由一处负责合并验证。

## 观察：交接合同比角色名字更重要

| 项目 | 好的交接 | 容易失败的交接 |
| --- | --- | --- |
| 输入 | 当前提交、文件和待答问题 | “看看项目” |
| 范围 | 只读；只检查保存失败 | “全面优化” |
| 输出 | 函数、反例、证据、验证命令 | “没问题” |
| 完成条件 | 两个失败路径均有检查 | “尽快完成” |
| 汇总规则 | 主任务复核，未知项保留未知 | 投票决定正确答案 |

子任务的摘要会压缩中间过程。要求把“测试已执行”和“建议执行测试”分开，避免主任务把建议抄成结果。报告中引用文件位置也不够：还应有触发条件与预期行为。

## 机制与源码：上下文边界与共享目录

**官方实现：** 固定版本同时包含多 Agent 的不同实现路径，本章源码导读聚焦 V2。[spawn.rs 的 fork_mode](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/handlers/multi_agents_v2/spawn.rs#L291) 接受 `fork_turns` 为 `none`、`all` 或正整数文本，并在省略时选 `all`。因此“子 Agent 天生没有历史上下文”并不准确；具体传入多少上下文要看所用接口和参数。

[会话多 Agent 提示](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/session/multi_agents.rs#L60) 明确描述共享目录。上下文分开不会自动生成 Git worktree，也不会给两个任务提供隔离的文件副本。需要独立修改时，应显式创建隔离的 checkout，或分配不会交叉的文件。

这也是为什么要在交接中重复关键约束：部分历史分叉可能没有带上早期决定；完整分叉则可能携带无关噪声。没有一种上下文模式能替代清晰的目标和验收合同。

## 可运行实验：两个工作者，一处验证

```sh
python3 scripts/course.py lab subagents
```

**教学简化：** [mechanisms.py](../../src/codex_lab/mechanisms.py) 用两个 Python `ThreadPoolExecutor` 工作者读取各自的数据副本。它们不是 Codex 子 Agent、不调用模型，也没有模拟模型推理。实验把“分发 → 独立结果 → 验证 → 汇总”的结构单独取出来。

预期 JSON 的 `verified_against_snapshot` 为 `true`。`open-work` 报告未完成任务 ID `[2, 3]`，`coverage` 报告具有 `test` 标签的任务 ID `[3]`。汇总会按 scope 稳定排序，不能依赖线程完成顺序。`aggregate_reviews()` 还检查 schema、scope 唯一性、ID 是否存在，以及结果是否符合源快照的谓词。

现在让报告引用一个不存在的任务：

```sh
PYTHONPATH=src python3 - <<'PY'
from codex_lab.mechanisms import SAMPLE_TASKS, audit_worker, aggregate_reviews
reports = [audit_worker(scope, SAMPLE_TASKS) for scope in ("open-work", "coverage")]
reports[0]["task_ids"].append(999)
try:
    aggregate_reviews(reports, SAMPLE_TASKS)
except ValueError as error:
    print(error)
else:
    raise SystemExit("invalid evidence was accepted")
PY
```

预期 `review cites an unknown task`。再把 `coverage` 的 ID 改成存在但不符合条件的 `[1]`，预期 `review evidence does not match the source snapshot`。检查“ID 存在”与“结论成立”是两道不同的关口。

## 怎样验证真实委派结果

真实代码审查没有上述固定谓词这么简单，但可以保留同样的结构。要求子 Agent 提供能执行的最小复现或测试；主任务读取相关实现并运行验证，再记录结果。若两份报告对同一输入给出冲突结论，不取多数意见，应比较输入、版本与命令，在同一个工作树复现。

并行仅在独立工作足够多时节省时间。两个 Agent 同时读一个十行函数可能比单任务更慢；主任务等待同一个接口决策时，多开 Agent 也不会解除依赖。实验不输出虚构的加速比。

## 故障排查

| 现象 | 优先处理 |
| --- | --- |
| 子任务重复同一工作 | 缩小问题并指定不重叠范围 |
| 主任务遗漏子任务结论 | 要求统一返回格式，检查所有预期 scope 是否齐全 |
| 并行修改互相覆盖 | 停止交叉写入，分配文件或独立 checkout，再审查差异 |
| 子任务说测试通过但无日志 | 将状态改为未证实，运行相应测试 |
| 没有出现子 Agent | 核实版本、功能和当前会话能力；保留单任务完成路径 |

## 练习与下一步

给离线报告删除一个 scope，再重复一个 scope，验证都被拒绝。然后为真实任务设计第三个独立问题：“CLI 错误信息是否包含可操作的修复建议？”说明它与保存正确性如何独立、最后由谁汇总。

下一章把验证合同接到脚本：[10 · 自动化与接口](10-automation.md)。
