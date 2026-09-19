# 05 · Skill：把重复的验收工作变成可执行流程

本章的产出是一次真实运行的 `taskboard-check` Skill 检查。你将区分 Skill 被发现、正文被加载、脚本被执行和任务被验收这四件事。我们使用项目内的教学 Skill，不安装或修改你的全局 Skill。

## 什么时候值得提取 Skill

在前三章中，我们反复检查 Taskboard 的 JSON 输出、标签过滤和测试证据。如果每次都重新讲一遍流程，就容易遗漏失败路径。把这个窄流程写成 Skill，可以让描述负责匹配任务，正文负责组织步骤，脚本负责可重复的机械检查。

`AGENTS.md` 适合「本项目持续遵守的规则」；Skill 适合「某类任务发生时才执行的一套流程」。Skill 不是新模型，也不是后台服务。脚本仍由普通执行工具运行，仍受当前权限限制。我们不把「在 Skill 里写了运行测试」当成「测试已经运行」。

## 认识交付的实例

```text
examples/taskboard/
  taskboard.py
  .agents/skills/taskboard-check/
    SKILL.md
    scripts/check.py
```

[Skill 源文件](../../examples/taskboard/.agents/skills/taskboard-check/SKILL.md) 的 frontmatter 包含 `name` 与 `description`。名字为 `taskboard-check`，描述说明仅用于这个课程的 CLI 验收。正文按读取实现、运行脚本、检查结果、报告边界组织；没有强行要求把每个 Python 问题都交给它。

**官方机制**是渐进加载：先提供 Skill 的名字、描述等元信息，选中后再读取完整正文；可用 `$taskboard-check` 显式指定，也可由 agent 根据描述匹配。仓库 Skill 的常用发现范围是当前目录到仓库根各层的 `.agents/skills`。因此，从课程根启动时不能假设位于子目录的 Skill 已经被发现；本章从 Taskboard 目录启动。[官方 Skill 指南](https://learn.chatgpt.com/docs/build-skills)

描述的质量影响发现后的选择。过宽的描述如「帮助处理所有开发任务」会抢占不相关任务；过窄而没有明确触发词又容易被漏掉。这里把目标写成「修改 add、list、标签或完成状态后验证 Taskboard」，读者能直接判断是否适用。

## 先脱离模型验证脚本

在课程根目录运行：

```bash
python3 examples/taskboard/.agents/skills/taskboard-check/scripts/check.py
```

预期返回码为 0，JSON 的 `status` 为 `passed`，并列出四项检查：

| 检查 | 怎样制造反例 |
| --- | --- |
| `normalized_add` | 输入带空白与重复的标签，确认归一为单个 `study` |
| `exact_tag_filter` | 同时存在 `study` 与 `studying`，只应选中前者 |
| `completion_and_status` | 完成任务后，保留标签且不再出现在 open 结果中 |
| `rejection_preserves_store` | 拒绝空标题，确认已有文件字节未变化 |

脚本在临时目录里创建数据文件，通过子进程调用实际 `taskboard.py`，最后删除临时数据。它不 mock CLI，也不调用模型。这证明的是本地程序的这些具体行为，不能证明真实 Codex 自动选中了 Skill，更不能代替完整回归测试。

脚本通过自身位置确定默认目标，因此切换 shell 当前目录不会悄悄测试另一个同名程序。验证练习副本时显式传目标：

```bash
python3 examples/taskboard/.agents/skills/taskboard-check/scripts/check.py \
  --target .local/taskboard-practice/taskboard.py
```

未实现标签的 starter 应失败。实现以后再运行应成功。失败退出码、错误信息和目标路径都要保留；不能为了让演示通过而改弱断言。

## 再让 Codex 使用完整流程

从课程根启动：

```bash
codex --cd examples/taskboard --sandbox workspace-write --ask-for-approval on-request
```

在 Codex 输入下面的任务；`$` 位于会话输入中，不是让 shell 展开变量：

```text
使用 $taskboard-check 验证当前 Taskboard。
先说明 Skill 的来源路径，运行其中脚本，报告具体检查结果和未覆盖范围。
不要修改实现；如果失败，保留失败证据并解释原因。
```

可以先用 `/skills` 查看可用列表。预期观察到的是 agent 阅读正文并运行脚本，而不是只复述名字。检查工具记录中的实际命令及退出码，再与脚本输出核对。Skill 名字出现在菜单中只证明发现成功；最终回答说「检查完成」还需要实际执行证据。[官方显式调用说明](https://learn.chatgpt.com/docs/build-skills)

自动匹配的对照任务是「请检查 Taskboard 的标签和完成状态是否符合约定」。它可能触发这个 Skill，也可能受其他指令、已安装 Skill 或模型决策影响。记录观察结果，不把一次成功或失败推成普遍规则。要稳定复现实验入口，优先用显式调用。

## 源码阅读与失效排查

固定版本的 [Skill 发现器](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/ext/skills/src/loader/discovery.rs) 负责扫描文件；[Skill 解析 crate](https://github.com/openai/codex/tree/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/skills/src) 处理元数据；[render.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/ext/skills/src/render.rs) 把可用 Skill 信息组织给模型。三个入口帮助区分「根本没找到」「文件格式不对」和「已经发现但未选用」。这些是**官方实现**；本课程提供的是应用层 Skill 实例。

若看不到 Skill，先检查启动目录、路径和 frontmatter，再开启新会话。若看到了但脚本不存在，检查正文里的相对路径如何解析。若脚本失败，先直接运行它，确认是实现不符合约定、Python 不可用，还是执行权限不足。仅修改 Skill 描述不会修复实际程序缺陷。

练习：在练习副本中故意把标签匹配改成子串匹配，再运行 Skill 脚本。`study` 错误选中 `studying` 时应失败。恢复实现后重跑。验收时说明这次检测依赖哪条断言，以及为什么「全部输出为合法 JSON」仍不足以发现这类语义错误。

下一章：[审批与执行隔离](06-safety.md)。
