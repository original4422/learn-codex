# 实验指南与验证分层

本页是实验索引，也是复现与排查手册。先从仓库根目录运行 `python3 scripts/course.py lab --help`；各实验追加 `--help` 可以查看参数。无需安装依赖，统一入口会把 `src/` 加入模块搜索路径。

## 实验清单

| 命令（前缀均为 `python3 scripts/course.py lab`） | 观察什么 | 验证性质 |
| --- | --- | --- |
| `loop` | 工具开始、返回与最终回答的因果顺序 | 固定脚本模型 |
| `loop --fail-tool` | 错误作为观察，不能冒充成功结果 | 离线失败注入 |
| `loop --max-tool-calls 0` | 工具预算耗尽时停止 | 离线预算检查 |
| `instructions` | home、根目录到 cwd 的候选文件与顺序 | 指令发现简化模型 |
| `policy --isolation workspace-write --approved` | 审批和执行边界分别满足 | 决策模拟，无 OS 沙箱 |
| `context` | 保留约束、决定和未完成工作 | 字符预算提取式压缩 |
| `subagents` | 独立快照、并行委派、证据汇总 | Python worker，无 Codex 子 Agent |
| `mcp-demo` | 初始化、列工具、调用有界读工具 | 真实 stdio MCP 子进程 |
| `probe` | 安装版本及必需 CLI 参数 | 真实 CLI，无模型 |
| `app-server` | initialize → initialized → thread/loaded/list | 真实 App Server，无模型 |
| `exec --allow-model` | JSONL 事件、结构化结果及事实校验 | 真实模型，需要认证 |

## 运行与读输出

```sh
python3 scripts/course.py lab instructions
python3 scripts/course.py lab context
python3 scripts/course.py lab subagents
python3 scripts/course.py lab mcp-demo
```

每份输出包含 `implementation` 或 `verification`，先读这一字段，再解释结果。`loop --fail-tool` 的最终状态可能为 `completed`，表示循环已结束并报告错误；它不表示业务工具成功。工具是否成功要检查事件里的 `ok`。

子 Agent 模拟的 `verified_against_snapshot: true` 仅表示本地汇总器对固定数据复算一致，不表示模型做过代码审查。MCP 演示的协议传输是真实进程间通信，但尚不是“模型自主选择该工具”的证据。

## 案例项目与练习起点

[参考实现](../../examples/taskboard/taskboard.py)包含 `add`、`list`、`done` 和标签过滤。它对不存在的存储返回空清单，对损坏的 JSON 明确失败；不会把损坏数据当作初始状态覆盖。测试覆盖旧数据兼容、空标题、未知任务、精确标签匹配、存储校验与原子替换失败。

第 1 章带你建立一个练习副本，在保留旧接口的前提下实现过滤。第 2 章检查失败和回归；第 5 章把验收流程收进可调用 Skill。不要直接编辑参考实现来伪造“练习通过”；保留起点与完成后的 diff 才能复盘。

```sh
python3 scripts/course.py test
python3 examples/taskboard/.agents/skills/taskboard-check/scripts/check.py
```

Skill 检查脚本是一组独立的 CLI 黑盒检查，可以作为完整测试之外的交叉证据；它不是完整测试套件的替代品。

## 可选安装

从仓库直接运行无需安装。若你想在虚拟环境里使用 `codex-lab` 命令，可安装本地包；构建工具可能需要访问包索引。

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/codex-lab loop
```

如果所在环境无法联网获取构建依赖，继续使用 `python3 scripts/course.py lab ...`。两条路径调用同一份代码。

## 真实 CLI 和模型路径

真实 CLI 适配器只在 `.cache/` 下保存课程运行状态，不读取你日常 Codex home 的历史。它对流设置总输出上限与超时，并在结束时回收子进程。源码见 [adapters.py](../../src/codex_lab/adapters.py)。

```sh
python3 scripts/course.py lab probe
python3 scripts/course.py lab app-server --timeout 15
python3 scripts/course.py lab exec --allow-model --timeout 120
```

模型实验要求读取固定样例，返回 `project`、`total_tasks`、`open_tasks`、`summary` 四个字段。程序同时检查进程退出码、`turn.completed`、错误事件、JSON 字段与数据中的实际计数。单有合法 JSON 不足以证明答案正确。

样例是三项任务，其中两项未完成。输出 JSON Schema 保存在 `.cache/real-exec/schema.json`，每次运行会先清除旧输出，再把收到的事件逐条刷新到 `events.jsonl`，最终消息在 `last-message.json`。超时时会保留本次已经收到的部分事件，但部分事件不能视为成功；以 CLI 错误、完成事件与结果校验共同判断。不要提交包含个人上下文的真实运行日志。

## 排查顺序

1. 确认工作目录、Python 版本与离线测试。离线失败通常是代码或输入问题，不应归咎于模型。
2. 运行 `probe`，确认 CLI 存在且参数兼容。版本漂移时先比较[来源说明](sources.md)。
3. 运行 `app-server`。协议握手失败与认证失败不同；查看超时、协议字段和本地进程状态。
4. 在隔离的 Codex home 中检查登录，再运行模型实验。认证、网络、额度和模型访问可能分别失败。
5. 若返回结构合法但计数错误，把它记录为事实验证失败，而不是调整校验器让它通过。

## 验证边界

本项目没有实现生产级 MCP 框架、操作系统沙箱、Codex 的 tokenizer 或完整 Agent 调度器。公开源码导读仍使用原生语言。课程的测试证明的是本仓库中明确列出的行为，真实产品行为由独立记录支持。交付时实际执行的命令与限制见[验收记录](acceptance.md)。
