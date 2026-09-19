# 06 · 审批与执行隔离是两件事

本章的目标是读懂一次拒绝：到底是请求没有获准，还是进程被执行隔离挡住，还是任务本身失败。你将用一个没有副作用的策略实验比较不同组合，再用真实 CLI 的配置观察边界。

## Taskboard 为什么也需要权限边界

给 `taskboard.py` 增加标签通常只需要读取项目文件、修改当前工作目录和运行 Python 测试。它不需要生产数据库、邮箱凭据或工作目录外的文件。权限应该和这个实际任务匹配。即使任务很小，shell 命令仍能启动任意程序；「请只修改一个文件」是指令约束，不能代替执行时的技术限制。

**审批策略**决定哪些动作必须先获得允许，审批者可能是用户或配置的自动审查。**OS 沙箱**限制执行进程实际可以访问的资源。**Git**保存和展示变更，方便恢复，但不阻止文件读取或网络发送。三个概念分别回答「是否允许」「能否执行」「改了什么」。

```text
工具请求
   |
   v
需要审批吗？ ---- 需要但未获准 ---> 拒绝 / 请求审批
   |
   v
选定的执行权限与 OS 沙箱
   |
   +---- 资源访问不允许 ----------> 执行失败 / 请求适当升级
   |
   v
命令本身运行 ----> 退出码、输出、文件变化 ----> 验收
```

此图是**教学简化**。实际实现还有执行规则、网络策略、缓存过的审批、工具种类差异以及托管限制。它不是对所有工具调用的完整顺序承诺。

## 先比较四种无副作用的情况

从课程根目录运行：

```bash
python3 scripts/course.py lab policy --approval ask --isolation read-only --action read
python3 scripts/course.py lab policy --approval never --isolation read-only --action write
python3 scripts/course.py lab policy --approval ask --isolation read-only --action write --approved
python3 scripts/course.py lab policy --approval ask --isolation workspace-write --action write --approved
```

读结果时分别看「审批决定」和「执行是否允许」。只读环境里的读操作可以通过；只读环境里的写操作不能因 `never` 就获得写权限。在实验中，单独给出 `--approved` 也不会改写隔离模式；因此已批准的写入仍可被只读隔离拒绝。可写工作区里的写操作则能符合两层约束。

这个实验完全不运行所描述的文件或网络动作。`ask` 是教学用参数，不是 Codex 的真实 CLI 枚举。实验故意要求所有写入先满足教学审批条件；真实 Codex 在工作区内的普通写入可能无需额外审批。实验也没有实现真实的权限升级：现实中的一次审批可以授权宿主为指定动作选择更宽的执行权限，但必须先经过相应策略。这里固定隔离模式，是为了把「批准一个请求」与「实际切换执行权限」拆开观察。

再运行：

```bash
python3 scripts/course.py lab policy --approval ask --isolation workspace-write --action network --approved
```

这次审批已满足，但 `isolation_allows` 仍为 false：可写工作区不代表开放网络。实验采用无网络默认值；真实实例的网络权限可能由配置和组织策略改变。不要用 Python 分支的结果声称已经测试了 macOS、Linux 或 Windows 的 OS 隔离。

## 真实 CLI 怎样表达这些选择

下面是固定版本 `0.155.1` 的显式启动方式：

```bash
codex --sandbox read-only --ask-for-approval on-request
codex --sandbox workspace-write --ask-for-approval on-request
codex --sandbox read-only --ask-for-approval never
```

第一个适合调查并在必要时提出审批；第二个允许在可写范围内开展编辑任务；第三个保留只读边界且不交互求批。`never` 表示不请求审批，不能读成「所有动作自动允许」。这两个参数的值和说明可用 `codex --help` 本地核对。

进入会话后用 `/status` 和 `/permissions` 查看当前配置与可选权限。观察到的有效配置才是本次运行的依据；不要因为书中有一条命令就假设组织策略允许它。`workspace-write` 也不等于目录中所有路径都可随意写入；固定版本会对 `.git`、已有 `.agents` 和 `.codex` 等敏感位置施加额外保护。[官方审批与安全说明](https://learn.chatgpt.com/docs/agent-approvals-security)

把真实任务限定为：

```text
读取 Taskboard 实现，解释标签过滤的入口。不修改文件。
如果读取失败，报告具体路径和错误；不要改权限来掩盖失败。
```

只读任务成功证明这次请求能在当前边界内完成；它没有验证写入阻止，也没有验证网络阻止。若要直接观察真实 OS 沙箱，可先阅读本机 `codex sandbox --help`，再在一次性目录中运行无害的读写探针。各系统和固定版本的命令形式存在差异，本课程不把跨平台命令猜测写成通用承诺。

## 从官方实现理解拒绝和重试

固定 commit 的 [tools/orchestrator.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/orchestrator.rs) 集中处理审批、沙箱选择与重试。沿调用进入 [sandboxing](https://github.com/openai/codex/tree/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/sandboxing/src)，可以看到平台执行策略；macOS 的 [seatbelt.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/sandboxing/src/seatbelt.rs) 是一个具体入口。

源码把批准决定和执行尝试建模为不同步骤，这正是实验分层的来源。课程没有重写完整安全系统，也不提供用前缀判断 shell 安全的「自制沙箱」。一个字符串以 `python` 开头，并不能说明它没有副作用；参数、脚本内容、工作目录和环境都会影响行为。

## 处理失败并保留证据

| 现象 | 先核对什么 | 合理的下一步 |
| --- | --- | --- |
| 缺少审批或审批被拒 | 实际请求、范围与拒绝理由 | 缩小动作，或说明需要的具体权限 |
| `Permission denied` | 路径、有效可写根、OS 错误 | 在已允许目录操作，保留原错误 |
| 测试退出非零 | stderr、失败断言、测试输入 | 修实现或修不成立的测试假设 |
| 下载失败 | 网络策略、DNS、目标服务 | 用已安装依赖继续独立工作，记录未验证项 |

不要把「测试失败」一律当成权限问题，也不要为了让输出变绿就扩大权限。Taskboard 本身不需要联网装依赖，离线的逻辑测试仍可完整执行。

练习：写出「不询问但仍只读」与「询问后仍失败」两个场景的解释。提交策略实验命令、输出和层次判断。若做真实沙箱探针，另记 OS、CLI 版本和进程退出状态；未运行的系统一律标记未验证。下一章将讨论 [会话与上下文](07-context.md)。
