# 机制实验室

这里的两个交互把控制流程变成可逐步观察的事件。它们在浏览器内运行，不联网、不执行 shell，也不调用真实模型。可编辑源码是 [app.js](../../site/assets/app.js)，命令行对应实验位于 [mechanisms.py](../../src/codex_lab/mechanisms.py)。

## 观察循环的终止条件

在下面选择成功、工具失败或预算耗尽，然后逐次点击“下一步”。注意决定是否执行工具，与工具实际成功是两个不同的时刻。错误结果也是观察信息，不能伪装成空结果继续回答。

实验结束后回答：哪一步有了外部证据？在哪一步可以得出“任务已完成”？若预算先耗尽，应该交付完整答案、部分结果，还是明确未完成？

```sh
python3 scripts/course.py lab loop
python3 scripts/course.py lab loop --fail-tool
python3 scripts/course.py lab loop --max-tool-calls 0
```

浏览器只演示状态变化；Python 版本输出事件，且有工具预算与失败路径测试。两者都属于**教学简化**。真实 Codex 的事件观察方法见[第 3 章](03-agent-loop.md)与[第 10 章](10-automation.md)。

## 把审批与隔离拆开

第二个交互让你独立切换“路径位于允许目录内”和“获得批准”。四种组合中只有两项均通过时，简化策略才允许执行。批准不能自动让越界路径变成可写；允许路径也不能自动代替业务批准。

```sh
python3 scripts/course.py lab policy --action write --isolation read-only --approved
python3 scripts/course.py lab policy --action write --isolation workspace-write
python3 scripts/course.py lab policy --action write --isolation workspace-write --approved
```

这段代码只是决策函数，未建立任何 OS 隔离。真实系统还可能有平台限制、网络策略与组织配置。把一次策略判断当成完整安全边界，是本实验希望你避免的误解。[第 6 章](06-safety.md)给出官方实现对应关系。

## 做一个预测，再验证

先不点击：写下你对四种权限组合的预期。逐一切换后，用一句话解释观察与你预期的差异。然后把这段解释应用到 Taskboard：写入清单需要什么路径能力，审查 diff 又需要什么能力？

如果交互按钮不可用，先确认浏览器允许 JavaScript；上面的 Python 命令提供等价的可运行入口。课程正文即使没有 JavaScript 也能阅读。
