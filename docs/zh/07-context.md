# 07 · 会话、上下文与压缩

## 学习目标

你将为 Taskboard 建立一份可恢复的任务交接，区分会话记录、模型当前上下文与磁盘文件；运行一个可解释的压缩实验，再理解它与固定版本 Codex 的差异。产出是一份包含约束、已做决定、未解决问题和验证命令的交接记录。

## 先实际使用：恢复同一个任务

在项目根目录启动 `codex`，给出任务：“阅读 Taskboard 的保存路径，只分析原子替换失败时如何保证原文件不损坏；记录结论和下一项测试，不修改代码。”完成一轮后保存会话 ID，退出，再恢复：

```sh
codex --version
codex resume
# 已记录明确的会话 ID 时，把下面的 ID 替换为实际值：
codex resume SESSION_ID
```

`codex resume --last` 适合只有一个明确目标的目录；并行做多个任务时，指定 ID 更容易复核。交互式恢复选择器默认按工作目录筛选，`--all` 可扩大范围；非交互执行则有自己的 `codex exec resume`。这些选项已通过本机 `0.155.1` 的帮助输出核对。[固定的 exec 恢复参数](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/exec/src/cli.rs#L151)

恢复后先说：“根据当前文件复核上次结论，再继续。”不要把模型记得的测试结果当作当前工作树的事实。如果另一位开发者改了 `save()`，旧会话仍可能保存旧结论。

## 观察：三份状态分别是什么

| 状态 | 包含什么 | 可靠的检查方式 |
| --- | --- | --- |
| 会话持久化记录 | 历史事件、恢复所需信息 | 记录会话 ID，使用恢复命令 |
| 当前模型上下文 | 本轮实际可见的历史、摘要、指令和工具结果 | 查看当前任务上下文与可见压缩事件，要求复核文件 |
| 磁盘工作树 | 最新代码、数据和 Git 差异 | `git diff`、读文件、重新运行测试 |

恢复会话不是 Git 回滚，压缩上下文也不是删除项目文件。模型可能看到摘要而非全部日志，所以交接应保留可追溯的文件与命令。Taskboard 的一份合格交接可以写成：

```text
目标：验证保存失败不会破坏已有数据。
约束：只改 Taskboard 和相关测试；不要打印凭据。
决定：标签使用归一化后的精确匹配。
证据：tests/test_taskboard.py；重新运行测试后填写结果。
未完成：模拟 os.replace 失败，并比较失败前后的文件字节。
下一步：运行针对保存失败的测试，审查 git diff。
```

这里的“约束”和“已验证事实”分开写；`待重跑` 不能抄成 `通过`。

## 机制与源码：压缩不是简单删前半段

**官方实现：** [ContextManager](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/context_manager/history.rs#L72) 区分模型窗口和保留的上下文状态；[恢复重建](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/session/rollout_reconstruction.rs#L12) 处理压缩检查点与后续记录。因而不能把恢复描述成“把所有聊天原样拼接”。

[CompactTask](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tasks/compact.rs#L29) 根据功能与提供方能力选择压缩路径。一个路径在[本地压缩编排](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/compact.rs#L244)中请求摘要并替换历史；另一个是[远程压缩](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/compact_remote_v2.rs#L223)。这里“本地”指客户端编排路径，不表示摘要完全不调用模型。

本教程不承诺固定上下文窗口大小、自动触发阈值或摘要逐字一致。它们与版本、模型、配置和提供方有关。手动压缩入口也应以当前客户端帮助为准；课程不通过填满上下文来制造模型消耗。

## 可运行实验：保护重要事实

从仓库根目录运行：

```sh
python3 scripts/course.py lab context
```

**教学简化：** `src/codex_lab/mechanisms.py` 中的 `compact_context()` 按字符预算抽取。它保留 `constraint`、`decision`、`open` 项，再保留放得下的近期普通消息。它不调用模型，不估算真正的 token，也不实现 Codex 的完整保留状态。

预期输出是 JSON：`after_chars` 小于 `before_chars`，`dropped_messages` 为 `1`，`memory` 仍包含“Never overwrite invalid JSON”“Tags use exact normalized matching”和待补的替换失败测试。长成功日志被删除，下一步读测试文件的消息保留。

再检查失败路径：

```sh
PYTHONPATH=src python3 - <<'PY'
from codex_lab.mechanisms import compact_context
try:
    compact_context([{"kind": "constraint", "text": "must survive"}], max_chars=3)
except ValueError as error:
    print(error)
else:
    raise SystemExit("expected a budget error")
PY
```

预期包含 `protected facts exceed budget`。程序选择显式失败，没有静默删掉约束。这是我们为教学实验定义的契约，不是对官方每条压缩路径的断言。

## 故障排查与验证

| 现象 | 优先检查 |
| --- | --- |
| 恢复选择器为空 | 当前目录、账户、Codex home 是否与原任务一致；是否用了 `--ephemeral` |
| 恢复后对代码的描述过时 | 对照当前文件和 Git 差异，重新运行测试 |
| 实验摘要比原文短却丢重要事项 | 是否把事项误标为普通 `message`；预算是否合理 |
| 模型压缩请求失败 | 记录真实错误与提供方配置；不要把离线实验通过记成服务恢复 |

完成本章应能复述：会话可恢复不等于每条原始日志都会再次发送给模型；文件事实由文件与测试证明。真实恢复和模型驱动压缩的执行状态见[验收报告](acceptance.md)。

## 练习与下一步

给实验加入一条“只读审查，不修改代码”的约束，再加入五条很长的工具日志。验证约束仍在、预算仍满足。随后故意让所有受保护项超过预算，说明为什么“让用户重新明确范围”比静默裁剪更可审查。

下一章为任务提供一个有界工具：[08 · MCP](08-mcp.md)。

继续实践：[第 10 章的离线压缩续写练习](10-automation.md)让你修复 compact ack 后提前续写的消费者，并区分压缩完成与续写业务验收。它使用固定虚构事件，不验证真实模型的摘要质量。
