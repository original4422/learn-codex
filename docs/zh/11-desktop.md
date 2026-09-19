# 11 · 桌面端：把同一个闭环放进可视工作区

## 学习目标

把 CLI 中的需求、文件、工具、测试、差异和恢复映射到桌面工作流；完成同一份 Taskboard 验收，而不依赖按钮位置记忆。桌面端是补充路径，课程的代码和检查命令仍由本地仓库提供。

## 先实际使用：准备一个干净练习副本

在课程根目录运行：

```sh
python3 examples/taskboard/prepare_exercise.py .local/taskboard-desktop
python3 examples/taskboard/acceptance.py --script .local/taskboard-desktop/taskboard.py
```

准备脚本拒绝覆盖已有目录；若你已做过本练习，请使用新目录名并同步修改后续路径。初始副本已有 add/list/done 与状态筛选，尚无标签功能。预期两个基础检查通过、两个标签检查失败。失败来自明确的待做需求，不是安装失败。

在桌面应用选择或打开 `learn-codex` 目录，新建本地任务，确认工作目录指向这份课程副本。当前官方桌面文档使用“ChatGPT desktop app”名称，具体入口与宿主版本可能不同；本课程按工作结果定位操作。[官方桌面入口](https://learn.chatgpt.com/docs/app)

输入：

```text
只修改 .local/taskboard-desktop/taskboard.py 和必要的同目录测试。
为 Taskboard 添加可重复的 --tag 参数和按完整标签筛选。
标签去掉首尾空白、转小写、去重；旧数据没有 tags 时按空列表处理。
先读现有程序和 examples/taskboard/acceptance.py，说明计划，然后实施。
运行：python3 examples/taskboard/acceptance.py --script .local/taskboard-desktop/taskboard.py
检查差异并总结验证结果；不推送、不部署、不发布。
```

课程提供的是可直接使用的桌面操作剧本；本项目的验收不把这段剧本当作已执行的桌面模型任务。用户自己的实际运行应记录客户端版本、工作目录和结果。

## 观察：CLI 与桌面各自在哪里看证据

| 闭环步骤 | CLI | 桌面端要找到的对象 |
| --- | --- | --- |
| 选工作范围 | `cd`、`codex -C` | 项目目录、任务运行环境 |
| 提交要求 | 输入提示或读取提示文件 | 消息与附件、被引用文件 |
| 观察执行 | 终端工具输出、JSONL | 工具执行记录、终端或任务活动 |
| 查看文件 | 编辑器、`cat`、`rg` | 文件预览或编辑面板 |
| 审查差异 | `git diff` | 差异面板及其比较基准 |
| 验证 | 运行验收命令并看退出码 | 相同命令的输出与退出状态 |
| 恢复 | 指定会话 ID 的 resume | 打开原任务并复核当前文件 |

不要只看模型最后一句“完成”。找到真正的命令、退出状态和当前文件。Taskboard 的练习副本在 `.local/`，被课程仓库忽略，因此根仓库的 Git diff 不会自动显示它；下一节给出适用于该副本的差异检查。

## 明确工作目录与差异基准

“本地”通常操作选定目录；“worktree”使用另一份 Git 工作树。开始前读出路径，结束时在同一个路径验收。如果用户在原目录运行测试，而 Agent 在 worktree 修改文件，两边看到的代码会不同。[官方 worktree 工作流](https://learn.chatgpt.com/docs/environments/git-worktrees)

练习副本的修改可与最初生成版本比较：

```sh
python3 examples/taskboard/prepare_exercise.py .local/taskboard-desktop-baseline
git diff --no-index -- .local/taskboard-desktop-baseline/taskboard.py .local/taskboard-desktop/taskboard.py
```

有差异时 `git diff --no-index` 的退出码为 1，这是“发现差异”，不是程序测试失败。基线目录也拒绝覆盖；重复练习使用新的名称。参考完成版是 `examples/taskboard/taskboard.py`，但审查时应先对照需求和测试，不直接把参考版复制过去当作自己的实现。

如果你选择在独立工作树练习，需在那里生成 `.local` 副本，因为被忽略的文件不会自动随 Git worktree 出现。课件、源代码、数据和任务聊天各有生命周期，不要假设它们总是同步移动。

## 机制与源码：公开服务边界，不推测私有 UI

**官方实现：** 公开 App Server 可以承载初始化、会话、轮次和事件；[初始化源码](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/app-server/src/request_processors/initialize_processor.rs#L49)是可读入口。这个事实不足以推断每个桌面按钮具体调用了哪个内部方法、桌面所有组件都开源或各客户端的功能完全一致。官方列出的开源范围见[组件说明](https://learn.chatgpt.com/docs/open-source)。

**教学对应：** 下图是工作流关系，不是桌面内部架构图。

```text
同一份需求与验收合同
        │
        ├── CLI：提示 → 工具输出 → 文件/测试/差异
        │
        └── 桌面：任务消息 → 执行活动 → 文件/测试/差异面板
                                        │
                                   同一 Taskboard 验收
```

工具权限也不因界面更友好而消失。审批说明应查看具体请求的命令和范围；[第 06 章](06-safety.md)关于审批与隔离的区分仍适用。这个课程不要求开启无限制执行。

## 可运行检查与预期结果

完成桌面任务后，在任务实际工作目录运行：

```sh
python3 examples/taskboard/acceptance.py --script .local/taskboard-desktop/taskboard.py
python3 scripts/course.py lab app-server
```

第一条预期四项验收通过，它验证你得到的代码。第二条预期真实 App Server 初始化及已加载任务列表读取成功，它验证公开协议可用；两项检查独立，后者不能替代前者，也不能证明桌面模型任务执行过。

给自己的桌面验收记录保留六项：客户端版本、实际工作目录、初始失败结果、最终通过结果、修改差异、剩余限制。若模型返回完成但代码没有变化，回到任务的执行记录寻找阻碍或目录偏差。

## 故障排查

| 现象 | 检查与处理 |
| --- | --- |
| 任务说改好了，终端仍是旧代码 | 核对本地/worktree 路径，进入真实修改目录 |
| Git diff 看不到练习改动 | `.local/` 被忽略；使用明确基线的 `--no-index` 比较 |
| 文件预览与终端结果不一致 | 刷新预览并核对绝对路径，以磁盘文件为准 |
| 审批后仍执行失败 | 看失败命令、OS 隔离和依赖；审批不是成功保证 |
| 客户端里找不到某按钮 | 按当前官方文档查入口；保留 CLI 验收路径 |

## 练习与课程收束

让桌面任务只读审查最终实现，要求给出一个真实反例或明确说明未发现问题；你自己运行它建议的验证。然后写一份不超过十行的交接记录，按[第 07 章](07-context.md)区分约束、决定、证据和未完成事项。

你现在可以用同一份合同跨客户端完成“要求 → 阅读 → 修改 → 验证 → 差异 → 复盘”。继续练习从[实验指南](labs.md)选择一项；本地 v1 的真实完成状态见[验收报告](acceptance.md)。
