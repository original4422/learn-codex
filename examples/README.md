# 可运行实验

[English](README.en.md)

所有命令从 learn-codex 仓库根目录运行，需要 Python 3.10 或更高版本。实验本身只用标准库。统一入口是 `python3 scripts/course.py lab <名称>`；等价入口是 `PYTHONPATH=src python3 -m codex_lab <名称>`。需要安装命令时可在自己的虚拟环境运行 `python3 -m pip install -e .`，随后使用 `codex-lab`。离线且未准备 setuptools 的环境直接使用统一入口，无须安装包。

## 贯穿案例：Taskboard

完成版在 `examples/taskboard/taskboard.py`。它是单写入者 JSON CLI，支持添加、查看、完成任务，以及标签过滤。原子替换防止半个 JSON 文件，不解决多个进程同时修改造成的更新丢失。

```sh
python3 examples/taskboard/taskboard.py --store .local/demo-tasks.json add "补充回归测试" --tag Study --tag test
python3 examples/taskboard/taskboard.py --store .local/demo-tasks.json list --tag study --status open
python3 examples/taskboard/taskboard.py --store .local/demo-tasks.json done 1
python3 examples/taskboard/acceptance.py
```

全新存储的第一条 ID 是 1，后续为已有最大 ID 加 1；重复运行不会清空数据。标签去除首尾空白、转小写、去重并排序，过滤按完整标签匹配。没有 `tags` 的旧数据读成空列表。标题长度为 1–200 字符，最多 20 个标签，每个 1–40 字符；错误退出码为 2。`--store` 必须放在子命令前。

开始真实修改练习：

```sh
python3 examples/taskboard/prepare_exercise.py .local/taskboard-practice
python3 .local/taskboard-practice/taskboard.py --store .local/practice-data.json add "读懂代码"
python3 examples/taskboard/acceptance.py --script .local/taskboard-practice/taskboard.py
```

准备脚本拒绝覆盖已有目录。验收临时数据写入目标脚本同目录的 `.cache/tmp`，因此在练习目录的 workspace-write 范围内即可运行。练习起点的 add/list/done 和状态过滤可以运行，但尚无标签；验收中的两项基础检查通过，两项标签检查失败是预期结果。让 Codex 在练习副本实现功能，随后重跑同一验收。参考版默认四项全部通过。最终实现的写入失败、损坏数据、ID 冲突等边界测试在 `tests/test_taskboard.py`。

## 机制实验与预期结果

```sh
python3 scripts/course.py lab loop
python3 scripts/course.py lab loop --fail-tool
python3 scripts/course.py lab loop --max-steps 1
python3 scripts/course.py lab instructions
python3 scripts/course.py lab policy --action write --approved --isolation read-only
python3 scripts/course.py lab context
python3 scripts/course.py lab subagents
```

| 实验 | 观察结果 | 明确边界 |
| --- | --- | --- |
| loop | 工具开始、工具结果、最终消息；两个未完成任务 | 脚本化 Mock，不评估模型能力 |
| loop --fail-tool | 工具错误进入观察，最终消息报告失败 | 不把异常伪装成成功数据 |
| loop --max-steps 1 | status 为 budget_exhausted | 步数和工具次数分别有上限 |
| instructions | 全局、根目录、子目录 override 的有序文本 | 显式根目录；无 Git 探测、配置解析或完整信任模型 |
| policy | approval_satisfied 为 true，isolation_allows 为 false | 纯决策表，没有安装 OS 沙箱；ask/never 是教学枚举 |
| context | 删除长工具输出，保留约束、决定、待办和最近消息 | 提取式摘要按字符计数，不是 Codex token/模型压缩 |
| subagents | 两个作用域的报告经原始快照交叉验证 | 独立 Python worker 模拟，不启动真实 Codex 子 Agent |

项目 AGENTS 发现中，空 `AGENTS.override.md` 会遮住同目录 `AGENTS.md`；全局发现跳过空文件。总字节预算会截断文本，不会拆坏 UTF-8 字符。实验只组合文本，不自动判断冲突指令的语义。

## 真正的 MCP stdio 实验

```sh
python3 scripts/course.py lab mcp-demo
python3 scripts/course.py lab mcp-server --root examples/mcp-data
```

`mcp-demo` 启动实际 Python 子进程，执行 initialize、notifications/initialized、tools/list、tools/call，返回 notes.md 的内容。第二条是等待客户端输入的服务器，正常情况下不会主动打印文字，可用 Ctrl-C 停止。每个消息是一行 JSON；stdout 仅供协议，不能插入日志。

`read_note` 只读根目录内的 `.md/.txt/.json`，每个文件最多 8192 字节；拒绝绝对路径、`..`、符号链接和越界。`task_stats` 接受同样路径约束，并验证 JSON 数组中 `done` 为布尔值后统计。协议错误用 JSON-RPC error；正常工具调用中发生读取失败用 `isError: true`。服务器不提供 HTTP、资源订阅和认证；只用于可信本地根目录，路径检查无法替代 OS 沙箱，也不防御另一进程同时替换目录的竞态。

要将此服务器接入真实 Codex，可在临时 CLI 配置中添加 stdio MCP 服务。保持项目绝对路径，Python 参数为 `-m codex_lab mcp-server --root <绝对根目录>`，并设置环境 `PYTHONPATH=<项目绝对路径>/src`。完整配置示例见课程 MCP 章节。本实验客户端通过不等于真实 Codex 已选择或调用过工具。

## 真实 CLI 与模型验证边界

```sh
python3 scripts/course.py lab probe
python3 scripts/course.py lab app-server
```

前者读取安装版本和帮助；后者启动真实 `codex app-server` 并执行 initialize → initialized → thread/loaded/list。两者均不调用模型。App Server 的消息格式与 MCP 不同，不能把其 method 或生命周期直接套给 MCP。状态文件限制在本项目 `.cache/codex-home`，临时文件在 `.cache/tmp`。

真实模型实验必须显式选择，可能产生模型用量：

```sh
CODEX_HOME="$PWD/.cache/codex-home" codex login
python3 scripts/course.py lab exec --allow-model --timeout 120
```

也可向这一进程提供已有 `CODEX_API_KEY`，不要把密钥写入仓库或日志。实验不读取或复制宿主机的 auth.json。可用 `--model <可用模型名>` 指定账户实际可用的模型。实际调用为 `codex exec --json --ephemeral --ignore-user-config --sandbox read-only --output-schema ...`；要求模型读取样本，随后检查完成事件、四字段最终 JSON 及总数 3、未完成数 2。JSONL 和最终输出写在 `.cache/real-exec`，检查前不要将它们作为公开素材，因为事件可能包含本机信息。

未加 `--allow-model`、无认证、超时、失败事件、错误 JSON、错误计数都会失败。Mock 和合成进程测试不会被记为真实模型验证。真实验证结果以仓库验收报告记录为准。

## 验证与排障

```sh
python3 -m unittest discover -s tests -v
python3 examples/taskboard/acceptance.py
```

找不到 codex 时先安装官方 CLI，再运行 probe。App Server 超时先核对 probe 版本和 stdio 参数，不要通过关闭沙箱来修复协议问题。实验目录已存在时另选路径。Taskboard 报损坏 JSON 时保留原文件，人工修复或选择新存储；不会自动清空。MCP 路径失败检查后缀、大小、根目录和符号链接。程序错误输出到 stderr，并返回非零退出码，自动化应检查退出码。
