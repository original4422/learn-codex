# 02 · 从「让它改代码」到可复查的开发闭环

上一章拿到了标签功能，本章把过程整理成能重复使用的方法。产出是一份短验收记录，包含需求、读过的关键实现、测试结果、diff 判断和恢复方案。工作流的每一步都应降低一个具体的不确定性。

## 把任务转成能反驳的要求

「支持标签」太宽，「输出里包含 study」又太弱。我们真正要确认的是：输入归一化、存储兼容、精确匹配、状态组合和失败不破坏数据。这些要求都能构造反例，因此可以验证。

| 未确定的问题 | 本项目的决定 | 能拒绝错误实现的检查 |
| --- | --- | --- |
| 大小写是否重要 | trim 后转小写 | ` Study ` 与 `study` 只保存一个标签 |
| 是子串还是精确匹配 | 精确匹配 | `study` 不匹配 `studying` |
| 旧任务怎么处理 | 缺失 tags 等于空列表 | 读取旧 JSON，原有 ID 不变 |
| 完成状态能否一起过滤 | 两个条件同时成立 | 已完成的 study 任务不出现在 open 列表 |
| 输入或存储损坏怎么办 | 报错，保留已有字节 | 无效 JSON 后调用 add，不得覆盖原文件 |

这些决定属于课程案例的产品行为，不是 Codex 官方默认。换一个真实项目时，首先替换这些决定，而不是复制提示词里的技术细节。

## 阅读顺序服务于改动范围

给 agent 的第一阶段任务可以是：

```text
先只读：找出 CLI 参数入口、JSON 加载/校验、保存和过滤函数。
按「输入 → 内存结构 → 持久化 → 输出」解释一次 add 和 list。
指出加标签会经过哪些边界；不要先重构。
```

在完成版中，对照 `main`、`load`、`validate`、`save`、`add` 和 `list_tasks`。模型若说「只加一个 argparse 参数就够了」，就用旧 JSON 兼容性追问它的数据路径。读取的目标是建立可检验的影响面，不是要求 agent 总结整个仓库。

你也可以自己查找：

```bash
rg -n '^def |add_argument|json\.' .local/taskboard-practice/taskboard.py
```

没有 `rg` 的机器直接打开该文件即可。工具选择不是学习目标；知道下一个问题该在哪段实现回答才是。

## 基线、针对性验收与回归各有职责

在开始时保存 `git status --short` 和初始验收结果。初始标签验收失败是已知差距，已有的 add/list/done 不应同时损坏。完成标签后运行相同验收，再检查课程的完整参考回归：

```bash
python3 examples/taskboard/acceptance.py --script .local/taskboard-practice/taskboard.py
python3 -m unittest discover -s tests -p 'test_taskboard.py' -v
```

**这两条命令测试的目标不同。** 第一条验收你的练习实现；第二条测试仓库交付的参考实现，包括更广的存储边界。不能拿第二条通过声称练习副本正确。若要扩展练习版的回归，新增直接指向练习实现的检查，或把适用测试移植到练习仓库。

检查器应优先覆盖可损害用户的边界。例如无效 JSON 不能被「读取失败就当空列表」吞掉，否则下一次添加会把原数据覆盖为只有一个新任务。测试应先写入无效内容，执行操作，确认非零退出和原字节完全一致；只检查异常类型会漏掉「先写坏再抛异常」。

Taskboard 使用同目录临时文件加原子替换来减少半写文件，但这是单写者案例。两个并发进程各自读同一版本再写回，仍可能丢更新。接受这个范围并写进复盘，比把「原子写」误说成完整事务系统更有用。

## Diff 是第二种证据

在课程根目录运行：

```bash
git -C .local/taskboard-practice diff --stat
git -C .local/taskboard-practice diff --check
git -C .local/taskboard-practice diff -- taskboard.py
git -C .local/taskboard-practice status --short
```

逐块检查时，把每块改动连回一个要求。新增 `tags` 默认值服务于旧数据；标签归一化服务于稳定存储与比较；list 中的两个条件服务于组合过滤。解释不出用途的块要继续检查，尤其是被顺手删除的错误处理和未经要求的依赖变更。

再给 Codex 一个审查提示：

```text
审查当前 diff 是否满足已确定的标签要求。
重点查旧 JSON、study/studying 精确匹配、错误输入后的文件字节保持。
每个问题给出具体输入、失败行为和相关位置；不要为了凑数量提出风格意见。
不要修改文件，先报告可复现的问题。
```

审查可以发现新的假设，但模型自审不是独立正确性证明。复现具体问题并添加相应断言，才把审查意见变成后续可重复的证据。没有发现问题时如实报告范围，不编造发现。

## 失败后缩小问题，不重做一切

若某项验收失败，先保留最小失败输入与输出。例如仅 `list --tag study --status open` 失败，就核对两个条件是 AND 还是 OR，再修改那一段。不要为一个布尔条件重写整个存储层。若是命令根本没启动，则优先查 cwd、解释器与权限；这不是实现缺陷的证据。

如果一次尝试走偏，先保存当前 diff：

```bash
git -C .local/taskboard-practice diff --binary > .local/taskboard-attempt.patch
git -C .local/taskboard-practice status --short
```

patch 不包含未跟踪文件，也不自动包含已经暂存的改动。重要的新文件需要另行保存，暂存内容需要单独查看 `git diff --cached`。确认只想丢弃自己在练习版 `taskboard.py` 上的未暂存改动后，才使用：

```bash
git -C .local/taskboard-practice restore -- taskboard.py
```

这是有意的恢复操作，会丢弃该文件的未暂存修改；不要把它用于有其他人工作或未保存成果的目录。你也可以保留失败副本，另建新名字的练习目录重新开始。课程准备脚本拒绝覆盖已有目标，防止不小心抹掉进展。

## 把工具能力与质量保证分开

固定版本的 [apply-patch crate](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/apply-patch/src/lib.rs) 展示补丁操作如何被解析与应用；[工具路由](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/router.rs) 展示工具调用如何分发。这些**官方实现**可以解释「修改怎样执行」，不能保证「修改符合你的需求」。需求、测试与 diff 组成的是我们在产品外建立的验证流程。

保存一份自己的记录，例如 `.local/workflow-notes.md`：

```text
需求：重复标签归一化；精确过滤；兼容旧数据；失败不破坏存储。
修改：列出受影响的函数及每个改动对应的要求。
检查：写实际命令、目标程序、退出状态和关键断言。
审查：记录已复现的问题、处理方式和仍未覆盖的边界。
恢复：基线提交及需要保留的未跟踪文件。
验证类型：真实模型编辑 / 本地参考验证 / 离线模拟，分别记录。
```

练习：在练习副本中实现一个错误的子串匹配，让验收失败，再只修这个缺陷。交付失败证据、最小 diff 和成功重跑。通过标准是别人能仅凭记录重复验证，而不是必须相信你的口头说明。下一章：[从工具调用理解 Agent 循环](03-agent-loop.md)。
