# 01 · 第一次任务：让 Taskboard 支持标签

本章要交付一个真实小改动：让命令行任务板保存标签，并按标签筛选任务。你会先运行基线，写明验收，再让 Codex 阅读、修改、测试，最后自己检查 diff。没有模型凭据也能运行参考实现和验收程序；这两条路径的验证结论不同。

## 准备 CLI 与认证

本课程需要 Python 3.10+ 和 Git。只读实验、网站和 Taskboard 不需要第三方 Python 依赖。真实 agent 路径额外需要 Codex CLI、可用认证与网络。先记录环境：

```bash
python3 --version
git --version
codex --version
```

课程源码基线是 `rust-v0.155.1`，公开 commit `be2951ea34f0d295ed0becf97079f92fa5f6950e`。若未安装 CLI，可以通过已有 npm 安装固定版本：

```bash
npm install -g @openai/codex@0.155.1
codex --version
```

没有 npm 时，可从 [固定官方 Release](https://github.com/openai/codex/releases/tag/rust-v0.155.1) 下载与系统和 CPU 架构匹配的二进制。官方还提供独立安装器与 Homebrew 路径，见 [CLI 安装说明](https://learn.chatgpt.com/docs/cli)。它们通常跟随最新版本；若使用不同版本，记录差异，不把本课程的固定源码当成新版本的实现保证。

本章的裸 `codex` 命令使用你日常的 Codex home；快速开始里的真实接口实验则使用隔离的 `.cache/codex-home`。这两处的登录状态不一定相同。若选择沿用隔离登录，可在课程根执行每条 Codex 命令时加前缀 `CODEX_HOME="$PWD/.cache/codex-home"`，包括后面的 `--cd` 启动命令，保持同一 home。

已有有效登录时无需重新登录。先检查状态，再按需选择一种认证方式：

```bash
codex login status
codex login
```

`codex login` 走浏览器的 ChatGPT 登录流程。若你选择 API Key 方式，先通过自己的安全环境提供 `OPENAI_API_KEY`，再运行：

```bash
printenv OPENAI_API_KEY | codex login --with-api-key
```

不要把 Key 字面量写进课程文件或命令历史。ChatGPT 登录与 API Key 是不同的计费和权限路径；实际可用性以账号与工作区为准。API Key 使用不等同于订阅内使用。[官方认证说明](https://learn.chatgpt.com/docs/auth)

CLI 的版本和登录状态是本地证据，不意味着网络、模型调用和账号额度已经可用。第一轮真实任务会检验这部分；失败时仍可以继续下面的离线路径。

## 先运行交付的参考实现

以下命令均从课程根目录执行。使用一个新的文件路径，第一次添加应得到 `id: 1`：

```bash
python3 examples/taskboard/taskboard.py --store .local/first-task.json add 'Learn the workflow' --tag study
python3 examples/taskboard/taskboard.py --store .local/first-task.json list --tag study
python3 examples/taskboard/taskboard.py --store .local/first-task.json done 1
```

第一条打印一个 JSON 对象，包含 `id`、`title`、`done: false` 和 `tags: ["study"]`；第二条打印包含该任务的数组；第三条把它变成 `done: true`。重复运行不会覆盖先前的任务，因此 ID 可能变大。不要删除自己的数据来追求和书中一致的数字；换一个新文件名即可。

这个完成版用于展示目标行为，不是让模型重复实现已存在的功能。真实编辑在独立练习副本中进行。

## 创建能回退的练习基线

```bash
python3 examples/taskboard/prepare_exercise.py .local/taskboard-practice
git -C .local/taskboard-practice init
git -C .local/taskboard-practice add taskboard.py AGENTS.md
git -C .local/taskboard-practice -c user.name='Course Learner' -c user.email='learner@example.invalid' commit -m 'Start Taskboard tag exercise'
python3 .local/taskboard-practice/taskboard.py --help
```

`prepare_exercise.py` 将可运行的 starter 复制为 `taskboard.py`。它保留添加、列举、完成任务和状态过滤，但尚无标签功能。这里的提交只在练习仓库保存基线；命令级作者配置不会更改你的 Git 全局配置。

先运行验收，确认它能指出缺失功能：

```bash
python3 examples/taskboard/acceptance.py --script .local/taskboard-practice/taskboard.py
```

此时非零退出是预期结果，原因应与缺少 `--tag` 和 `tags` 字段有关。若是找不到 Python、文件或语法错误，先修环境；那不是我们要教学的功能差距。再检查完成版通过同一套要求：

```bash
python3 examples/taskboard/acceptance.py --script examples/taskboard/taskboard.py
```

这构成一个有价值的验收器：它既能接受参考行为，也能拒绝已知缺陷。把测试跑绿但从未确认它能检出错误，会降低我们对测试的信任。

## 把验收标准交给 Codex

启动练习目录中的 CLI：

```bash
codex --cd .local/taskboard-practice --sandbox workspace-write --ask-for-approval on-request
```

在会话里输入：

```text
为当前 Taskboard 添加标签功能。验收标准已经确定，请先读取 AGENTS.md
和 taskboard.py，说明需要改动的位置，然后完成实现、测试和 diff 检查。

1. add 支持重复的 --tag；标签去首尾空白、转小写、去重并排序。
2. 每个标签 1–40 个字符，最多 20 个；拒绝无效值且不改坏原数据。
3. list --tag 精确匹配归一化后的标签，且可与 --status open/done/all 组合。
4. 旧 JSON 中没有 tags 的任务仍可读取，并视为没有标签。
5. 保留已有任务 ID、add/list/done 行为和 JSON stdout 接口。
6. 只使用 Python 标准库；不要修改课程中的参考实现或验收程序。

从练习目录运行验收：
python3 ../../examples/taskboard/acceptance.py --script taskboard.py

完成后报告改了什么、实际执行的检查及退出状态、仍未验证的行为。
```

需求中的「标签」包含数据格式、输入规范和组合过滤三个层面。把它们写清楚后，Codex 才能针对边界实现；「帮我加一个好用的标签功能」会留下大小写、重复值和旧数据兼容等未定义选择。

本章先明确验收再编辑，并不要求对已经授权的小修改反复请求批准。若真实出现权限审批，阅读具体命令及范围；其机制在 [第六章](06-safety.md) 解释。

## 自己收齐完成证据

退出或暂停 CLI 后，在课程根运行：

```bash
python3 examples/taskboard/acceptance.py --script .local/taskboard-practice/taskboard.py
git -C .local/taskboard-practice diff --check
git -C .local/taskboard-practice diff -- taskboard.py
git -C .local/taskboard-practice status --short
```

验收成功说明覆盖到的行为符合要求；`diff --check` 检查空白等补丁问题；普通 diff 帮你判断变更是否合理；status 能发现未跟踪的新文件。还要阅读实现，确认没有硬编码验收数据、删除失败路径或更改不相关文件。

这次任务的交付是修改后的 `taskboard.py`、可解释的 diff、验收输出和一次简短复盘。不要只保存模型的「完成」一句话。若你没有运行真实 Codex，只运行了参考实现与验收，记录为「本地程序验证通过，真实模型编辑未验证」。

## 机制与失败路径

**官方实现**中，[TUI 参数](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/tui/src/cli.rs) 把启动选项传入交互客户端，[login crate](https://github.com/openai/codex/tree/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/login/src) 提供认证相关能力。Taskboard 与验收器是课程自建程序，不是 Codex 内置能力。

若 `codex` 不在 PATH，先修安装路径，别重复安装多个版本掩盖问题。若登录成功但调用失败，保存错误类型与退出状态，核对账号、服务和网络。若模型直接修改了参考实现而非练习目录，检查 `--cd` 与 diff，不接受这次范围错误。若验收失败，让 agent 针对第一条失败断言解释输入、预期与实际值，再修复。

练习：在成功版本中创建两个标签分别为 `study` 和 `studying` 的任务，确认筛选前者不会误选后者。说明为什么这比「列表输出里出现 study」更严格。下一章：[形成完整开发闭环](02-workflow.md)。
