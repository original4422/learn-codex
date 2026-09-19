# 04 · AGENTS.md：把项目约定放到正确位置

本章完成后，你能预测一组指令文件的发现顺序，并为 Taskboard 写出短小、可执行的项目约定。`AGENTS.md` 适合放持续有效的工作要求，例如测试入口和数据格式约束；当前任务的验收标准仍应写在任务本身。

## 先看我们真正需要的约定

Taskboard 只依赖 Python 标准库，读写 JSON，命令输出也为 JSON。给它加标签时，如果 agent 顺手引入一个 ORM 或把普通日志写到 stdout，即使演示看起来正常，也会破坏项目的可复现性和脚本接口。用下面这样的规则表达约束，比「写高质量代码」更容易检查：

```markdown
# Taskboard working agreements

- Keep runtime dependencies in the Python standard library.
- Preserve JSON output on stdout; send diagnostics to stderr.
- Preserve existing task IDs when adding fields.
- Run the documented acceptance check after changing CLI behavior.
- Report the command, exit status, and any unverified assumptions.
```

这些是**项目指令**，不是操作系统权限。文件中写「不要联网」可以指导 agent，但不能代替网络隔离。也不应把 API Key、账号密码或生产数据写进指令文件。

## 指令发现：目录路径比文件名更重要

**官方行为**：启动时先选 Codex home 中的全局指导，再从项目根沿路径走到当前工作目录。每层优先检查 `AGENTS.override.md`，再检查 `AGENTS.md`，最后检查配置过的 fallback 文件名；每层最多纳入一个文件，按根到当前目录拼接。默认项目文档预算为 32 KiB。更近的目录提供更具体的规则。不要把这理解成对整个仓库递归加载所有同名文件。[官方 AGENTS.md 指南](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

```text
repo/AGENTS.md                 通用规则
repo/app/AGENTS.md             同层有 override 时被替代
repo/app/AGENTS.override.md    app 的特定规则
repo/other/AGENTS.md           从 app 启动时不在路径上
```

如果从 `repo/app` 启动，路径包含根和 app；如果从 `repo` 启动，app 是子目录，不在启动发现链中。agent 之后为了修改子目录可以读取其约定，但不要把「可能主动读取」当成「启动时已经自动注入」。要让重要模块规则稳定参与任务，选择明确的启动目录，并要求操作前检查目标目录的指导文件。

`override` 替代的是同目录候选文件，不是自动抹掉所有祖先规则。子目录若只写「这里使用另一条测试命令」，并不意味着允许违反根目录的数据兼容要求。指令是自然语言上下文，不是一个会对每条句子自动求解冲突的类型系统；明确冲突时应指出来源和适用范围，不能悄悄选择最方便的解释。

## 用夹具验证自己的预测

从课程根目录运行：

```bash
python3 scripts/course.py lab instructions
python3 scripts/course.py lab instructions --max-bytes 80
```

实验使用仓库中的 `examples/instructions` 夹具，全局目录也是夹具，不会读取或改写你的个人设置。默认结果依序列出选中的文件与各自文本；小预算运行展示截断后信息的损失。先手写你预测的路径顺序，再与 JSON 结果比较。重点观察 `AGENTS.override.md` 是否排除了同层普通文件，以及旁支目录是否缺席。

需要改变扫描起点时：

```bash
python3 scripts/course.py lab instructions \
  --root examples/instructions/repo \
  --cwd examples/instructions/repo \
  --home examples/instructions/home
```

与默认 app 起点比较，根目录启动不应包含 app 层的文件。这个 Python 实验是**教学简化**：根、home 和字节预算由命令显式给定；它没有完整复刻 Codex 的配置合并、工作树识别、平台路径处理和全部回退选项。不要把实验的默认 2048 字节当成官方默认值。

## 用真实 Codex 做一次只读核对

在课程根目录运行下面的命令，查看真实实例如何说明它的项目约定：

```bash
codex --cd examples/taskboard --sandbox read-only --ask-for-approval on-request \
  'List the instruction files relevant to this working directory. Read and summarize their concrete test and data-format requirements. Do not change files.'
```

这个命令会使用你实际的个人配置；和夹具不同，结果可能包含个人约定。只记录路径和与本项目相关的规则，不要公开整个用户配置或会话。模型的口头总结是一个观察点，不能单独证明每个字节已被注入。结合实际文件、当前目录以及必要时的本地日志来核对。[官方指南的验证与排错说明](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

读固定版本的 [agents_md.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/agents_md.rs)，先找候选文件顺序和目录遍历，再看字节上限和测试。不要先逐行阅读整个 core；用「为什么旁支文件没有加载」这个问题限定搜索范围。源码是**官方实现**，本地夹具输出是**观察到的实验行为**。

固定版本还有一个值得验证的边界：项目扫描先选首个存在的普通文件，再读取内容；所以空的 `AGENTS.override.md` 仍会遮住同层 `AGENTS.md`，之后空内容被忽略。全局 provider 则会继续寻找首个非空文件。另一个前提是项目信任状态：本版本对标记为不可信的项目跳过项目指导。遇到差异时以固定源码和实际信任配置为证据，不把文档的概括当作所有边界情形。

## 失效时怎么查

规则没生效，先确认 `pwd`、仓库根和启动参数。再检查是否有覆盖文件、文件是否为空、是否超出文档预算。更新指导后开启新运行，避免误把旧会话的已有上下文当成新配置。若模型读到了规则但没有遵守，这是执行质量问题，应通过实际验收暴露；继续堆更多同义规则通常没有帮助。

练习：在一次性练习副本里添加一个不在当前路径的目录和 `AGENTS.md`，验证默认发现结果不变。再把工作目录改到该目录，预测并核对变化。最后为 Taskboard 添加一条能用命令验证的约定，例如「错误输入不覆盖已有 JSON」。验收要求是你能给出发现顺序、规则适用范围和验证命令，而不仅仅说「创建了 AGENTS.md」。

下一章：[把重复工作封装成 Skill](05-skills.md)。
