# v1 本地验收记录

验收日期：2026-09-19。目标是按[已确认任务书](../../PROJECT_BRIEF.md)交付完整本地教学项目。上游固定为 Codex CLI `0.155.1`，对应 commit `be2951ea34f0d295ed0becf97079f92fa5f6950e`。本页与[机器可读记录](../../reports/verification.json)共同说明检查范围；详细输出保存在[检查日志](../../reports/checks.log)。

## 交付范围

| 任务书要求 | 对应产物与验收方式 |
| --- | --- |
| 独立本地 Git 仓库、中英文入口 | 根目录 README、README.en.md，Git 提交历史 |
| 完整双语课程与指南 | 每种语言 19 页，含 11 个正式章节；页面清单与正文检查 |
| 真实贯穿项目 | Taskboard 参考实现、可运行 starter、练习生成器与黑盒验收 |
| 机制解释与可运行实验 | 工具循环、指令发现、策略、上下文、并行汇总；明确简化边界 |
| 真实接口集成 | MCP stdio 子进程、Codex exec 适配器与 App Server 客户端 |
| 图解与双语网站 | Python 生成 SVG、交互实验、搜索、章节语言切换、响应式导航 |
| 验证、来源与贡献说明 | 自动检查、固定源码哈希、源码地图、双语贡献指南 |

## 本次实际结果

| 检查 | 结果 |
| --- | --- |
| 自动测试 | 63 项通过，含双语覆盖、失败路径和进程回收 |
| Taskboard 黑盒验收 | 参考实现 4/4；起点版本被正确拒绝 |
| Skill 独立检查 | 4 项行为检查通过 |
| 网站构建 | 39 个 HTML 页面，1550 个本地链接与资源引用通过 |
| 安装后运行 | 项目内新虚拟环境 editable 安装成功，`codex-lab loop` 通过 |
| 固定源码核对 | 28 个已记录文件的 SHA-256 全部一致 |
| 真实 CLI 与 App Server | 均通过，不调用模型 |
| 真实模型 | 尝试超时，未验证；不计入通过项 |

## 验证分层

**离线程序与协议**：行为测试覆盖正常结果、故意失败、预算耗尽、旧数据兼容、原子写入失败、MCP 输入与路径边界、子进程异常和超时回收。另有独立 Skill 黑盒检查。练习起点运行正常但不能通过标签功能验收；参考实现通过同一验收，这是验收器能够拒绝已知缺陷的证据。

**真实本地 Codex**：本机 `codex --version` 返回 `codex-cli 0.155.1`；必需 exec 参数检查通过；真实 App Server 完成 `initialize → initialized → thread/loaded/list`，返回空的已加载会话列表。这使用的是项目内隔离的 Codex home，不调用模型。

**真实模型**：尝试了 `python3 scripts/course.py lab exec --allow-model --timeout 20`，结果为退出码 2、`subprocess deadline exceeded`。当前进程没有可用的 `OPENAI_API_KEY`、`CODEX_API_KEY` 或 `CODEX_ACCESS_TOKEN`，课程隔离 home 中也未建立登录。超时本身不能证明唯一根因。没有得到成功完成事件与经过事实校验的模型结果，故真实模型编辑、真实模型 MCP 调用、真实 Codex 子 Agent 协作均标记为**未验证**。

**网站**：按用户要求参考 OpenAI 的黑白灰与简洁无衬线排版，保留独立 learn-codex 标识。构建生成两种语言全部页面，根路径直接展示中文。内部链接、锚点、源码下载链接与静态资源由构建器检查。浏览器交互与视口检查的实际结果见机器记录中的浏览器条目。

## 本地复现

在仓库根目录运行：

```sh
python3 scripts/course.py check
python3 examples/taskboard/acceptance.py
python3 scripts/course.py lab mcp-demo
python3 scripts/course.py lab probe
python3 scripts/course.py lab app-server
python3 scripts/course.py serve --port 8765
```

打开 [本地预览](http://127.0.0.1:8765)，检查首页中文、英文切换与同章对应；用搜索找 `MCP`；在机制实验室观察失败和预算终止；进入章节标记进度并切换语言；在窄屏打开目录。复查源码时，可用侧栏旁的 Markdown 源文链接。

要重新生成不包含模型调用的执行记录，运行：

```sh
python3 scripts/verify.py --with-codex
```

没有安装 Codex 时省略 `--with-codex`，记录会清楚显示哪些集成未运行。真实模型需要按[实验指南](labs.md)完成认证后另行执行，不能由本命令替代。

## 已知限制

- 本次运行环境为 macOS arm64、Python 3.14.7；代码面向 Python 3.10+，但没有声称运行了每个 Python 版本、Linux 或 Windows。
- Taskboard 是单写入者示例。原子替换可防止半截 JSON，不提供多写入者事务或防止并发丢更新。
- MCP 服务是本地可信目录上的有界教学子集；路径检查不抵御恶意并发文件替换，也不等同 OS 沙箱。
- Python 策略、压缩与子 Agent 实验为教学模型；没有验证真实跨平台隔离、模型压缩质量或模型委派质量。
- SDK 提供源码导读和用途比较；可运行的最小集成选择 App Server，不声称另外实测了 TypeScript/Python SDK。
- 官方网站是动态资料，固定的是源码 commit 和本次核实日期；未来文档或 CLI 变化需重新核验。

## 发布边界

产物只保存在 `learn-codex`。未修改相邻项目，未创建公开仓库、推送远端、公开部署或发布社媒。预览服务只绑定 `127.0.0.1`。用户可根据上述材料验收本地 v1，并在具备认证后补充真实模型运行证据。
