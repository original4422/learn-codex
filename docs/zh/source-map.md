# 概念与源码地图

从一个行为追到一个入口，再验证一个不变量。以下链接全部固定到 `rust-v0.155.1` 的提交 `be2951ea34f0d295ed0becf97079f92fa5f6950e`，不是随时变化的 main 分支。版本证据见[来源与版本](sources.md)。

## 按问题查找

| 你观察到的问题 | 固定源码入口 | 重点符号或职责 | 课程 |
| --- | --- | --- | --- |
| 第一次运行 | [main.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/cli/src/main.rs#L1) | CLI 参数分派 | [01](01-first-task.md) |
| 一个请求为什么会调用多个工具 | [turn.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/session/turn.rs#L163) | run_turn → run_sampling_request | [03](03-agent-loop.md) |
| 工具如何分派 | [router.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/router.rs#L74) | ToolRouter | [03](03-agent-loop.md) |
| 工作目录的指令 | [agents_md.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/agents_md.rs#L55) | load_project_instructions → agents_md_paths | [04](04-instructions.md) |
| 全局指令 | [mod.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/codex-home/src/instructions/mod.rs#L24) | load_from_codex_home | [04](04-instructions.md) |
| Skill 发现 | [discovery.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/ext/skills/src/loader/discovery.rs#L1) | 搜索来源与根目录 | [05](05-skills.md) |
| Skill 内容 | [render.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/ext/skills/src/render.rs#L1) | 把 Skill 信息呈现给模型 | [05](05-skills.md) |
| 执行与审批 | [orchestrator.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/orchestrator.rs#L1) | 工具执行编排 | [06](06-safety.md) |
| 审批不等于沙箱 | [sandboxing.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/sandboxing.rs#L194) | default_exec_approval_requirement | [06](06-safety.md) |
| 恢复会话 | [rollout_reconstruction.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/session/rollout_reconstruction.rs#L12) | RolloutReconstruction | [07](07-context.md) |
| 压缩路由 | [compact.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tasks/compact.rs#L29) | 按能力与功能选择路径 | [07](07-context.md) |
| 压缩后的模型窗口 | [history.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/context_manager/history.rs#L72) | ContextManager | [07](07-context.md) |
| MCP 连接 | [rmcp_client.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/rmcp-client/src/rmcp_client.rs#L609) | initialize → list_tools → call_tool | [08](08-mcp.md) |
| MCP 调用分派 | [mcp.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/handlers/mcp.rs#L176) | handle_call | [08](08-mcp.md) |
| 子 Agent 上下文 | [spawn.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/handlers/multi_agents_v2/spawn.rs#L291) | fork_mode | [09](09-subagents.md) |
| 共享目录边界 | [multi_agents.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/session/multi_agents.rs#L60) | 共享文件系统与上下文提示 | [09](09-subagents.md) |
| JSONL 事件 | [exec_events.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/exec/src/exec_events.rs#L11) | ThreadEvent | [10](10-automation.md) |
| 事件到输出 | [event_processor_with_jsonl_output.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/exec/src/event_processor_with_jsonl_output.rs#L1) | JSONL 输出处理器 | [10](10-automation.md) |
| App Server 握手 | [initialize_processor.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/app-server/src/request_processors/initialize_processor.rs#L49) | initialize | [10](10-automation.md) |
| TypeScript SDK | [exec.ts](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/sdk/typescript/src/exec.ts#L91) | CodexExec.run 启动 CLI | [10](10-automation.md) |
| Python SDK | [client.py](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/sdk/python/src/openai_codex/client.py#L215) | JSON-RPC client | [10](10-automation.md) |

## 一次源码阅读应该留下什么

以恢复会话为例：先写出问题“关闭终端后，为什么还能接着任务做？”；再定位恢复类型与持久化历史重建；最后区分磁盘日志、模型输入窗口、当前工作树。三者不是一份数据。你应能指出哪个函数重建历史，并给出“恢复会话不会撤回文件修改”的本地检查办法。

读大型函数时只跟踪相关输入、分支与输出。例如在 `tasks/compact.rs` 中，先看到功能开关分支，再看到远程压缩能力匹配。由此可以否定“每种模型都执行同一段摘要算法”，但还不足以计算某账户何时自动压缩；后者需要运行配置、模型信息与真实事件。

## 哪些是教学代码

| 本仓库代码 | 用来观察 | 有意省略 |
| --- | --- | --- |
| `src/codex_lab/mechanisms.py` | 循环、指令发现、审批与隔离、压缩、汇总验证 | 网络模型、完整配置层、实际 OS 沙箱 |
| `src/codex_lab/mcp_server.py` | stdio MCP 请求生命周期与有界文件工具 | 远程认证、完整协议能力与生产部署 |
| `src/codex_lab/adapters.py` | CLI JSONL、结构化输出、App Server 握手 | 生产重试、完整 UI 客户端 |
| `examples/taskboard/taskboard.py` | 一个能测试与审查的真实程序 | 多写者数据库事务与部署 |

这些文件没有被描绘成 Codex 的 Python 重写。阅读原生实现时保留 Rust、TypeScript、Python SDK 各自的边界。桌面章节没有私有界面源码链接；公开 App Server 协议只说明可集成的服务边界。

## 练习：证据链检查

任选一行，写下“主张、固定源码、可运行命令、可观察结果、仍未证明的部分”五项。如果只有文件名而说不出函数的输入输出，缩小问题。如果本机版本不同，先记录差异，再决定重跑哪个实验；不要悄悄把链接换成 main。
