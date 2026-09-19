# 03 · 从一次工具调用看懂 Agent 循环

本章的产出是一份能解释的事件记录：你能指出谁提出动作、谁执行动作、结果怎样回到模型，以及为什么「回答结束」不等于「修改正确」。先完成 [第一次任务](01-first-task.md)，再把界面里的读文件、运行测试和修改文件还原成循环。

## 从 Taskboard 的失败测试出发

假设你要求给任务加标签。Codex 先读取 `taskboard.py`，再运行验收测试。测试提示 `--tag` 不被识别。模型据此选择修改参数解析，工具执行修改并返回结果；模型继续运行测试，直到获得足够证据或遇到无法继续的阻碍。

这里有三个不同的角色。模型根据当前上下文选择下一步；宿主程序负责工具注册、参数解释、执行控制和结果归档；Python、shell、文件系统等工具产生外部事实。模型说「准备运行测试」只是意图，工具返回的退出码才是执行事实，而测试断言决定它实际验证了什么。

```text
用户目标 + 项目指令 + 已有事件
                 |
                 v
          模型选择下一步
            /          \
      请求工具          输出回答
         |                  |
    权限检查/执行           本轮结束
         |
    结果或错误事件
         |
         +------> 更新上下文，继续选择
```

这张图刻意省略流式传输、并发调用、上下文压缩和取消，是**教学简化**。它帮助解释反馈关系，不宣称 Codex 原生循环由这几行 Python 实现。

## 先运行可控的小循环

从课程根目录运行：

```bash
python3 scripts/course.py lab loop
python3 scripts/course.py lab loop --fail-tool
python3 scripts/course.py lab loop --max-steps 1
```

第一个运行输出带教学标记的 JSON 事件，包含工具请求、返回结果和终止状态。第二个让工具故意失败：错误应成为可检查的反馈，不能伪装成成功。这里最终 `status: completed` 只表示脚本循环以报告错误的回答结束；工具事件的 `ok: false` 才说明业务读取失败。第三个故意耗尽步数预算，结果应说明已达到上限，不能生成一个凭空的「已完成」。具体字段以输出和 [实验指南](labs.md) 为准。

这个实验的「模型」是一段确定性脚本。它在固定输入上作出固定选择，便于测试工具反馈和终止条件；它没有调用 OpenAI，也没有证明真实模型会正确完成标签需求。它的教学价值在于：只要把工具失败丢掉，或忘记循环预算，就能稳定重现一个控制层错误。

阅读实验时先找三个位置：产生下一动作的函数、真正执行工具的分支、检测停止条件的分支。把其中任何一个混进另一个，通常会让故障无法定位。例如，在工具适配层把异常替换成空列表，会让模型无法区分「没有任务」和「读取失败」。

## 再观察真实 CLI 的公开事件

本节需要已认证的 Codex 和可用网络，可能产生模型使用费用。在课程根目录运行只读任务：

```bash
mkdir -p .local
codex exec --sandbox read-only --json \
  'Read examples/taskboard/taskboard.py. Explain how list filtering works. Do not edit files.' \
  > .local/read-events.jsonl
```

终端的进度信息可能走标准错误；`--json` 的标准输出是逐行 JSON。不要把两个流混成一个 JSON 文件。先检查命令退出状态，再阅读事件：

```bash
python3 - <<'PY'
import json
from pathlib import Path
for line in Path('.local/read-events.jsonl').read_text().splitlines():
    event = json.loads(line)
    item = event.get('item', {})
    print(event.get('type'), item.get('type', ''), item.get('status', ''))
PY
```

官方非交互接口会报告线程、轮次和条目的生命周期；条目可表示助手消息、命令执行等。不要要求模型每次都选同一种工具，也不要依赖字段出现的固定顺序。较小文件可能通过一种读法读取，另一次可能通过另一种工具读取；有些请求无需工具。可靠的判断是「我所需要的证据是否出现」，而非「事件序列是否和截图一模一样」。[官方非交互模式](https://learn.chatgpt.com/docs/non-interactive-mode)

Taskboard 修改完成后，理想的证据链是：实际读取了相关实现 → 发生了目标文件修改 → 实际运行验收命令 → 验收退出为 0 → diff 与需求一致。`turn.completed` 只能说明轮次结束；模型仍可能漏测或误解需求。不要把一个成功退出的解释任务当成代码验收。

## 对照固定版本源码

本课程固定公开 CLI `rust-v0.155.1`，commit `be2951ea34f0d295ed0becf97079f92fa5f6950e`。从 [core/session/turn.rs](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/session/turn.rs) 追踪轮次推进，从 [工具目录](https://github.com/openai/codex/tree/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools) 追踪调用分发，再读 [exec 目录](https://github.com/openai/codex/tree/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/exec/src) 看非交互客户端怎样呈现事件。

这些是**官方实现**的阅读入口；不要试图从客户端代码推导服务端模型的内部推理。界面输出、公开事件和命令退出状态是我们能观察的边界。课程的 Python 循环只复现请求—执行—反馈的控制关系，没有实现官方协议全集。

## 故障诊断与练习

若事件文件为空，先检查 CLI 标准错误、登录状态和网络；不要立即怀疑 JSON 解析器。若已经有部分事件但最后失败，保留失败记录并检查是否存在工具错误或认证错误。若工具运行很久，先看当前命令及其输入，区分等待 stdin、长测试和进程卡住。

练习：比较默认实验与 `--fail-tool`，写出第一个发生分歧的事件。然后把循环预算设为 1，解释为什么「尚未完成」是正确结果。验收要求是能分别举出模型决策错误、工具执行错误、宿主控制错误，而不是笼统写成「AI 不稳定」。若你另外运行了真实 CLI，单独记下版本、命令、退出状态和证据文件；离线实验结果与真实事件保持分开。

下一章：[把项目约定放到正确位置](04-instructions.md)。
