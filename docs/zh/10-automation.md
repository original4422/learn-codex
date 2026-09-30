# 10 · 自动化：从终端输出到可验证的接口

## 学习目标

用非交互 CLI 为 Taskboard 生成结构化摘要；区分事件流与最终 JSON；运行真正的 App Server 握手；知道何时选择 CLI、SDK 或 App Server。交付物必须同时有过程证据、最终结果和语义检查，不能只有一段看起来像 JSON 的回答。

## 先选择接口

| 需求 | 合适入口 | 你负责的部分 |
| --- | --- | --- |
| 一次脚本任务或 CI 步骤 | `codex exec` | 输入、超时、退出码、结果验证 |
| 在应用代码中连续运行任务 | Codex SDK | 会话生命周期、错误处理、应用业务规则 |
| 自己做客户端、审批 UI、事件面板 | `codex app-server` | 初始化、请求关联、通知、审批与取消 |
| 把外部能力给 Codex 用 | MCP 服务 | 工具合同与服务端边界，见上一章 |

MCP 是“把工具接给 Agent”；App Server 是“你的客户端驱动 Codex”。两者不能因都传 JSON 就互换。官方分别提供 [SDK](https://learn.chatgpt.com/docs/codex-sdk) 与 [App Server](https://learn.chatgpt.com/docs/app-server) 的用途说明。

## 实际使用：结构化的 Taskboard 摘要

先做无需模型的接口检查：

```sh
python3 scripts/course.py lab probe
```

预期识别本机版本，确认 `--json`、`--output-schema`、`--ephemeral` 等参数，并确认 App Server 支持 stdio。它只执行帮助命令。

然后显式启动模型实验：

```sh
python3 scripts/course.py lab exec --allow-model --timeout 120
# 需要指定已获账户支持的模型时：
python3 scripts/course.py lab exec --allow-model --model YOUR_AVAILABLE_MODEL
```

第二条的模型名需要换成实际可用名称，不承诺所有账户共享默认模型。实验使用真正的 `codex exec --json --output-schema ... --sandbox read-only`；提示要求读取 `examples/taskboard/sample.json`，不修改项目。课程程序启动 Codex，不直接调用 Responses API。

**认证边界：** 适配器把 CLI 状态放在本项目忽略目录 `.cache/codex-home`，不会自动使用全局 Codex home 中的登录。你可以通过已有安全凭据供应方式仅为该进程提供 `CODEX_API_KEY`，或在这个隔离环境进行交互登录：

```sh
PYTHONPATH=src python3 - <<'PY'
import subprocess
from codex_lab.adapters import codex_binary, local_environment
subprocess.run([codex_binary(), "login"], env=local_environment(), check=True)
PY
```

登录需要用户在浏览器完成正常认证；不要把 auth 文件或 Key 复制到教程、版本库或报告。该运行可能产生模型用量。没有可用凭据时记录失败，仍可完成后面的握手与所有离线检查。

## 观察：事件和答案是两个输出

[非交互模式](https://learn.chatgpt.com/docs/non-interactive-mode)支持 JSONL 事件和最终结构化输出。本课程分别保存在忽略目录 `.cache/real-exec/`：

| 文件 | 作用 | 检查 |
| --- | --- | --- |
| `schema.json` | 请求的最终结果形状 | 四个必填字段，不允许额外字段 |
| `events.jsonl` | 逐行事件过程 | 有完成事件，没有致命失败 |
| `last-message.json` | 最终答案 | 能解析，类型正确，计数与文件一致 |

预期最终对象包含 `project="taskboard"`、`total_tasks=3`、`open_tasks=2` 和非空 `summary`。摘要文字可以变化；三个数据值必须与样本相符。`--output-schema` 约束形状，不证明答案真实，所以 `validate_summary()` 再做语义验证。

JSONL 每行一个对象，不是一个大的 JSON 数组。`item.completed` 表示某个条目结束，不能直接等同整轮成功；工具条目本身也可能失败。真正的模型实验只有在进程成功、出现 `turn.completed`、无致命失败、最终对象通过数据验证时才返回成功。事件格式见固定的 [ThreadEvent](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/exec/src/exec_events.rs#L11)。

## 最小真实集成：App Server 无模型握手

```sh
python3 scripts/course.py lab app-server --timeout 15
```

[适配器](../../src/codex_lab/adapters.py) 启动真实 `codex app-server --listen stdio://`，发送以下生命周期：

```text
initialize(id=1, clientInfo) → result(userAgent, ...)
initialized notification
thread/loaded/list(id=2) → result(data, ...)
terminate child process
```

预期得到 `initialize.userAgent` 和 `loaded_threads`，新启动的隔离服务通常没有已加载会话。这证明真实程序启动、双向通信和初始化后的读取有效。没有发送 `thread/start` 或 `turn/start`，所以没有进行模型推理，也没有验证模型工具执行。

App Server 的通知名是 `initialized`，上一章 MCP 的通知名是 `notifications/initialized`。即使都采用逐行 JSON，也应按各自接口发送。客户端必须按 ID 关联响应，不能假设“下一行一定是我的响应”；中间可能有通知。实现会限制 stdout 总量、设置超时、在结束时回收子进程，防止演示变成永久后台服务。[固定的初始化处理器](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/app-server/src/request_processors/initialize_processor.rs#L49)

如果继续构建完整客户端，还需处理 `thread/start`、`turn/start`、通知流、用户审批请求、取消和连接中断。仅完成握手不够成为生产客户端。

## SDK 对应什么机制

**官方实现：** 固定版本的 [TypeScript CodexExec.run](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/sdk/typescript/src/exec.ts#L91) 启动 CLI 并消费事件；[Thread.run](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/sdk/typescript/src/thread.ts#L118) 汇总条目与最终回答。相比之下，[Python CodexClient](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/sdk/python/src/openai_codex/client.py#L215) 使用 App Server stdio JSON-RPC。这说明“SDK 一定直接发模型 API”并不成立。

官方 TypeScript 使用方式可以表示为以下代码，属于接口示例；本课程没有把安装 npm 包或运行该片段记入已完成验证：

```typescript
import { Codex } from "@openai/codex-sdk";
const codex = new Codex();
const thread = codex.startThread({
  sandboxMode: "read-only",
  workingDirectory: process.cwd(),
});
const result = await thread.run("Read examples/taskboard/sample.json and count open tasks.");
console.log(result.finalResponse);
```

当需要这个方向时，在独立目录按官方文档安装 SDK、记录实际包版本，再接入同样的业务验证。不要假设源码仓库的开发占位包版本就是可安装的 npm 发布版本。

## 可运行的结果拒绝实验

```sh
PYTHONPATH=src python3 - <<'PY'
from codex_lab.adapters import validate_summary
for wrong in (True, 99):
    try:
        validate_summary({"project":"taskboard","total_tasks":3,
                          "open_tasks":wrong,"summary":"Looks valid."})
    except ValueError as error:
        print(error)
    else:
        raise SystemExit("bad count was accepted")
PY
```

布尔值在 Python 中是 int 的子类，因此验证使用精确类型检查；`True` 应被拒绝，整数 `99` 也应因与样本不符而拒绝。这个测试不调用模型，专门验证消费者没有盲信 schema 或自然语言。

## 离线练习：压缩确认后，什么时候才能续写？

本练习补充 App Server 的异步边界，不重复 CLI 的事件实验。**固定版本官方实现**中，[压缩处理器](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/app-server/src/request_processors/thread_processor.rs#L2407)提交 `Op::Compact` 后返回 `{}`；[官方测试](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/app-server/tests/suite/v2/compaction.rs#L224)另外等待压缩 item 完成和对应 turn 结束。因此 RPC ack 不能直接作为发送续写请求的依据。

**教学简化：** [四个案例](../../examples/completion/cases.json)是固定虚构事件的字段投影，只包含消费函数要读的字段，不是完整 wire schema 或真实模型日志。调用者已知目标 thread、压缩与续写的 RPC ID，以及历史 `prior_turn_ids`；只有一个 pending 手动压缩请求，没有其他新的压缩任务竞争。消费函数从目标 thread 的第一个非历史 `contextCompaction` 开始事件绑定当前 item/turn，不能从空 ack 推导 turn ID。这个合同不用于判定任意并发会话日志。

复制有缺陷的消费函数到新的练习目录，再运行课程目录中的可信验收器：

```sh
mkdir -p .local
mkdir .local/completion-practice &&
  cp examples/completion/starter.py .local/completion-practice/consumer.py
python3 examples/completion/acceptance.py --script .local/completion-practice/consumer.py
# 对照参考实现：
python3 examples/completion/acceptance.py
```

练习目录必须尚不存在，避免覆盖已做的修改。starter 应退出 1：`first_failure` 指向 `ack-is-not-completion` 的前缀 1，期望 `wait`，实际 `continue`。参考实现应退出 0。

只修复 `progress(events, context)`。输入是从空前缀开始、逐步增长的事件列表；函数每次重新计算状态，不修改输入，只返回四种动作：

| 动作 | 含义 |
| --- | --- |
| `wait` | 当前证据不足，继续读取事件 |
| `continue` | 已收到 compact ack、绑定的压缩 item 完成及同 turn 的 `completed` 终态，可以发送一次续写 |
| `verify` | 由续写 RPC 响应绑定的 turn 已正常结束，可以进行业务验收 |
| `failed` | 目标 RPC 失败，或绑定的 turn 为 `failed` / `interrupted` |

`continue` 是状态而非可重复执行的命令；本案例由调用者只发送一次续写，随后把其响应加入事件序列。学生函数不能返回“业务成功”。

| 案例 | 必须识别的边界 |
| --- | --- |
| 只有 compact ack | 保持 `wait` |
| 混入旧 turn、其他 thread、错误 item 的完成事件 | 不借用无关证据；目标 item 完成后仍等目标 turn，续写轮另行绑定 |
| compact item 完成，随后 turn interrupted | 先 `wait`，再 `failed` |
| compact turn completed，但缺少目标 item 完成 | 保持 `wait` |

验收器逐个前缀比较期望动作，报告第一处错误推进。正常续写案例随后分别给出正确摘要和 `open_tasks=99`；外部宿主复用 `validate_summary()`，必须一通过、一拒绝。两个答案共享同一条成功事件序列，说明 turn 结束并不决定任务是否正确。保留修复 diff，并说明 starter 为什么提前续写、错误计数又由谁拒绝。

这条命令导入你自己的练习文件执行；它是本地教学验收，不是运行不可信代码的沙箱。全程不启动 Codex、不连接 App Server、不调用模型。

## 故障排查与练习

| 现象 | 含义与下一步 |
| --- | --- |
| `codex` 不在 PATH | 安装官方 CLI，再运行 probe |
| 认证或网络失败 | 保存实际失败类别；隔离 home 不会继承全局登录 |
| 超时 | 本轮未完成，不能使用旧答案；检查模型/网络并显式重试 |
| schema 正确但计数错误 | 业务验证失败；对照输入文件，不放宽校验使其“通过” |
| App Server 握手成功 | 只证明协议层；继续查看真实模型测试状态 |

练习：给 Taskboard 新增第四条任务，先预测当前 `validate_summary()` 为什么会拒绝新计数。再把验证改为从所用快照计算预期值，并增加“使用了错误快照”的失败测试。不要只把常量从 3 改成 4。

下一章将同一闭环映射到[桌面端](11-desktop.md)。实际执行记录统一见[验收报告](acceptance.md)。
