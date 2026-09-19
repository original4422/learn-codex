# 来源与版本：把可核实的边界写清楚

本课程于 **2026-09-19** 核对官方文档，以本机 `codex-cli 0.155.1` 对应的公开版本为源码基线。课程命令首先适用于这个版本；安装较新版本后，请先执行 `codex --version` 和相关子命令的 `--help`。

## 固定上游

| 项目 | 已核实值 |
| --- | --- |
| 官方仓库 | [openai/codex](https://github.com/openai/codex) |
| 发布标签 | [rust-v0.155.1](https://github.com/openai/codex/releases/tag/rust-v0.155.1) |
| 完整提交 | [be2951ea34f0d295ed0becf97079f92fa5f6950e](https://github.com/openai/codex/commit/be2951ea34f0d295ed0becf97079f92fa5f6950e) |
| 注解标签对象 | `4e21628f9ec9ee656650cd2b62ef92225725b5ac` |
| 上游许可证 | Apache-2.0 |
| 机器可读记录 | [references/upstream.json](../../references/upstream.json) |

**观察到的行为：** 本机版本输出为 `codex-cli 0.155.1`；`git ls-remote` 返回标签对象和上述 peeled commit；取得的源码中 `codex-rs/Cargo.toml` 也记录 `0.155.1`。源码归档 SHA-256 为 `cd5a884836b53422052989479c6662f06e2ee8bb768c1a86a5ff7326b887d4d6`。这些检查建立版本对应关系，不代表已编译整个上游或测试所有功能。

```sh
git ls-remote https://github.com/openai/codex.git \
  refs/tags/rust-v0.155.1 'refs/tags/rust-v0.155.1^{}'
codex --version
```

## 三种证据不能混用

| 标识 | 可以支持什么 | 不能支持什么 |
| --- | --- | --- |
| 官方实现 | 固定提交中的类型、分支、状态转换 | 所有用户账户都能调用某模型 |
| 观察到的行为 | 本次运行的命令、输入、输出与退出码 | 未运行的平台和未尝试的异常路径 |
| 教学简化 | Python 实验定义的不变量和失败行为 | Codex 使用同样的算法、字数预算或线程模型 |

课程实验使用原创的小型 Taskboard 项目。离线规划器是固定脚本；上下文压缩是抽取；子 Agent 实验是 Python 工作者。它们帮助观察控制流，不复刻模型推理，也不是 Codex 模型测试。真实 CLI、真实 App Server 握手、真实模型请求分开记录在[本地验收](acceptance.md)中。

## 官方入口与文档漂移

实施时实际打开了[开源组件说明](https://learn.chatgpt.com/docs/open-source)、[非交互执行](https://learn.chatgpt.com/docs/non-interactive-mode)、[MCP](https://learn.chatgpt.com/docs/extend/mcp)、[子 Agent](https://learn.chatgpt.com/docs/agent-configuration/subagents)、[SDK](https://learn.chatgpt.com/docs/codex-sdk)、[App Server](https://learn.chatgpt.com/docs/app-server)和[桌面应用](https://learn.chatgpt.com/docs/app)。旧的 `developers.openai.com/codex/` 入口在核查日重定向到 `learn.chatgpt.com/docs`。

网页是持续更新的产品文档，提交链接是固定的源码。两者发生差异时，先注明版本：例如本提交 SDK 位于 `sdk/typescript/` 和 `sdk/python/`，不能把某个网页展示的移动分支路径当成历史版本的文件位置。当前桌面文档还使用 ChatGPT desktop app 名称；本教程按任务书称“桌面端”，讲工作流，不据此推断私有 UI 实现。

## 复查源码的最短路线

先打开[源码地图](source-map.md)，按正在观察的行为读一个入口和一个测试，而不是通读整个 Rust 仓库。每个链接都固定到同一提交；`references/upstream.json` 保存所读文件的内容散列。`.cache/upstream/` 是实施时下载的忽略目录，不是课程安装要求，也不会随 Git 提交。离线课程不依赖它。

下载上游时先遇到本地代理不可连接及沙箱 DNS 限制，随后通过获准的只读网络下载取得源码。没有因此换成未经核实的文件路径，也没有修改系统代理配置。

## 引用与许可证

正文以原创解释、实验和短源码定位为主，不复制整份官方文档。上游代码归 OpenAI 及其贡献者所有，适用其 Apache-2.0 许可证。本地 `.cache` 中的完整上游材料保留原有许可证。课程不声称属于 OpenAI 官方培训，也不把公开 CLI、SDK、App Server 的可见性扩大到桌面私有 UI 或服务端模型。贡献时请在变更中记录新的版本、证据和未验证项，参见[贡献指南](contributing.md)。
