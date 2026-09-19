# 08 · MCP：给 Agent 一个有边界的工具

## 学习目标

把 Taskboard 的资料读取封装为本地 stdio 工具，观察初始化、工具发现和调用的完整往返；拒绝越界路径、符号链接和过大文件。你会区分“模型选择了工具”“协议传输了请求”“工具执行了操作”三个证据层。

## 先实际使用：运行独立工具进程

从仓库根目录运行：

```sh
python3 scripts/course.py lab mcp-demo
```

这会启动本仓库的 Python MCP 服务子进程，完成 `initialize` → `notifications/initialized` → `tools/list` → `tools/call`，读取 `examples/mcp-data/notes.md`，然后结束进程。无需 Codex 登录，也不请求模型。

**观察目标：** 输出应显示服务信息、包含 `read_note` 与 `task_stats` 的工具列表、成功的文本结果。这是实际进程和标准输入输出上的协议通信；客户端直接指定调用，不能据此说模型学会了选工具。

## 观察协议：消息有不同职责

```text
客户端                     本地服务
  initialize (id=1)   ───→  协商版本与能力
                      ←─── result (id=1)
  notifications/initialized → 进入可调用状态
  tools/list (id=2)   ───→  返回工具定义和 inputSchema
                      ←─── result (id=2)
  tools/call (id=3)   ───→  校验参数，再执行有界读取
                      ←─── content / isError
```

请求有 ID，回应使用相同 ID；通知没有 ID，不等待回复。工具业务失败可返回 `result.isError=true`，错误 JSON-RPC 请求则返回 `error` 对象。把两类失败都当“模型失败”会丢失真正的排查线索。

**教学实现：** [mcp_server.py](../../src/codex_lab/mcp_server.py) 只实现课程用到的有界子集：逐行 JSON、初始化、ping、工具列表、工具调用。没有 HTTP、OAuth、资源订阅或生产级并发。标准输出只写协议 JSON；调试信息应走标准错误，避免破坏消息流。

## 工具合同：边界必须在代码里

| 工具 | 输入 | 成功结果 | 失败边界 |
| --- | --- | --- | --- |
| `read_note` | `{"path":"notes.md"}` | UTF-8 文本 | 绝对路径、`..`、符号链接、非允许后缀、超过 8192 字节 |
| `task_stats` | 指向 JSON 任务数组的相对路径 | total/open/done | 除读取边界外，还拒绝非数组及非布尔 done |

根目录在服务启动时指定，不由模型在每次调用中选择。`readOnlyHint` 等注解用于描述工具，不负责强制安全；真正的限制来自 `bounded_read()` 的检查。即使模型说“为了完成任务请读取根目录外的文件”，服务仍应拒绝。

路径检查也不是 OS 沙箱：它适用于可信的本地数据目录，不抵御另一个进程在检查和读取之间恶意替换目录的竞态。若要承载不可信并发写入，应先改变部署隔离与文件访问方案，不能把这个教学服务直接宣传成安全网关。

## 接入真实 Codex：一次性配置

[官方 MCP 文档](https://learn.chatgpt.com/docs/extend/mcp) 描述本地 stdio 与 HTTP 连接。这里使用一次性 `-c` 配置，不需要更改用户全局配置。在仓库根目录启动：

```sh
codex \
  -c 'mcp_servers.course.command="python3"' \
  -c "mcp_servers.course.args=[\"$PWD/scripts/course.py\",\"lab\",\"mcp-server\",\"--root\",\"$PWD/examples/mcp-data\"]" \
  -c 'mcp_servers.course.required=true'
```

上述命令假定项目路径不包含双引号或反斜线；包含特殊字符时，把经过 TOML 转义的绝对路径写入配置。进入会话后查看 `/mcp`，再要求：“用 course 的 read_note 读取 notes.md，并依据工具返回内容概括；不要使用 shell 代读。”核对调用轨迹中的工具名、参数与结果。若回答中没有工具调用证据，本次只能算文本回答。

这一步需要可用的 Codex 认证、模型和 MCP 工具能力，可能产生模型用量。`required=true` 让连接失败显式暴露；它不是“所有工具调用都会成功”的保证。课程验收报告分别记录独立协议演示和真实模型工具使用状态。

## 机制与源码：发现、分派、执行分开读

**官方实现：** 固定版本的 [RmcpClient](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/rmcp-client/src/rmcp_client.rs#L609) 有初始化、工具发现、调用接口；[MCP handler](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/handlers/mcp.rs#L176) 把 Agent 工具调用接入执行路径。Python 服务是外部工具提供方，不是把 Rust 客户端翻译成 Python。

从 `tools/list` 的参数 schema 开始读，再追踪 `tools/call` 的工具名与参数。模型看到的工具说明帮助它决定调用；服务端仍必须验证类型、字段和边界。MCP 本身不会让任意工具自动获得权限，也不会把外部文本升级为可信指令。

## 可运行失败实验

下面验证越界请求返回工具错误，同时服务仍能回应：

```sh
PYTHONPATH=src python3 - <<'PY'
from codex_lab.mcp_server import Server
s = Server("examples/mcp-data")
s.dispatch({"jsonrpc":"2.0","id":1,"method":"initialize","params":{
    "protocolVersion":"2025-11-25","capabilities":{},
    "clientInfo":{"name":"course-check","version":"1"}}})
s.dispatch({"jsonrpc":"2.0","method":"notifications/initialized"})
r = s.dispatch({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{
    "name":"read_note","arguments":{"path":"../taskboard/sample.json"}}})
assert r["result"]["isError"] is True
assert "result" in s.dispatch({"jsonrpc":"2.0","id":3,"method":"ping"})
print(r["result"]["content"][0]["text"])
PY
```

预期包含 `parent traversal are forbidden`。这个实验直接调用 Python 分派器来精确检查拒绝分支；前面的 `mcp-demo` 才检查实际子进程传输。两者互补。

## 故障排查

| 现象 | 检查 |
| --- | --- |
| 工具列表为空或初始化失败 | Python 路径、工作目录、`--root` 是否存在；是否完成 initialized 通知 |
| 客户端报 JSON 解析错误 | 服务是否把日志打印到 stdout；是否按一行一个 JSON 输出 |
| 文件明明存在却拒绝 | 是否有符号链接、后缀不允许、路径越界或文件过大 |
| 能列工具但模型没调用 | 提示是否指定任务与工具、是否真的出现调用事件；列工具不等于用工具 |

## 练习与下一步

在 `examples/mcp-data/` 的实验副本放一个 `tasks.json`，包含一条完成和两条未完成任务，调用 `task_stats`，预期 `total=3, open=2, done=1`。再把一个 `done` 改成字符串 `"false"`，预期工具错误而不是把非空字符串当成真值。测试时保留输入与失败结果。

接下来把彼此独立的审查任务委派出去：[09 · 子 Agent](09-subagents.md)。
