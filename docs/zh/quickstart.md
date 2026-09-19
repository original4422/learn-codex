# 快速开始：先运行，再深入

目标是在不依赖模型认证的情况下，先确认课程、实验与案例都能在你的机器运行，然后再开始一次真实 Codex 任务。所有命令都从仓库根目录执行。

## 1. 检查环境

课程需要 Python 3.10 或更新版本，以及用于审查差异的 Git。网站生成与离线实验只使用 Python 标准库，不需要 Node、数据库或第三方运行依赖。

```sh
python3 --version
git --version
python3 scripts/course.py check
```

`check` 运行行为测试，构建中英文网站，并校验本地链接。成功会以 `OK` 和网站页数、链接数结束。测试数量可能随着项目更新变化，当前交付的确切数量写在[验收记录](acceptance.md)。

## 2. 运行第一个循环

```sh
python3 scripts/course.py lab loop
python3 scripts/course.py lab loop --fail-tool
python3 scripts/course.py lab loop --max-tool-calls 0
```

观察三个输出里工具结果、错误与预算终止的区别。它们使用固定脚本代替模型；目的是让失败路径可重复。不要把三条命令的成功退出理解为三次真实模型调用。

## 3. 运行 Taskboard

```sh
mkdir -p .cache
python3 examples/taskboard/taskboard.py --store .cache/quickstart.json add "阅读首次任务" --tag study
python3 examples/taskboard/taskboard.py --store .cache/quickstart.json list --tag study
python3 examples/taskboard/.agents/skills/taskboard-check/scripts/check.py
```

第一次创建存储文件时任务编号为 1；再次执行 `add` 会新增任务，而不是覆盖旧任务。最后一条命令在临时存储中检查标签匹配、完成状态和非法输入，不修改你的清单。若想重做，从一个新的 `--store` 文件名开始即可。

## 4. 打开双语网站

```sh
python3 scripts/course.py serve --port 8765
```

浏览器打开 [http://127.0.0.1:8765](http://127.0.0.1:8765)。首次页面与导航为中文。右上角 `English` 切换同一页面；按 `/` 搜索，按 `Esc` 关闭。窄屏用目录按钮打开章节导航。按 Ctrl-C 停止服务。

服务器只绑定本机地址。`dist/` 是可重新生成的静态产物，Markdown 源文件在 `docs/`。请通过 HTTP 预览，不直接双击 HTML；全文搜索需要读取本地索引。

## 5. 接入真实 Codex

课程按 `0.155.1` 编写。已有 CLI 时先核对版本；尚未安装时，可用 npm 安装指定版本，或按[官方 CLI 指南](https://learn.chatgpt.com/docs/cli)选择适合你的平台的安装方式。

```sh
npm install -g @openai/codex@0.155.1
codex --version
python3 scripts/course.py lab probe
python3 scripts/course.py lab app-server
```

`probe` 检查本地 CLI 能力，`app-server` 启动真实 CLI 并完成协议握手，两者均不调用模型。安装 npm 包需要可用的 Node/npm 与联网条件；这不是离线课程本身的依赖。

真实调用需认证。为了隔离课程缓存，下面仅为单条命令设置项目内的 Codex home，不改变你的日常设置。认证文件不会进入 Git。

```sh
CODEX_HOME="$PWD/.cache/codex-home" codex login
CODEX_HOME="$PWD/.cache/codex-home" codex login status
python3 scripts/course.py lab exec --allow-model
```

登录方式与账户可用范围以[官方认证文档](https://learn.chatgpt.com/docs/auth)为准。认证成功也不代表网络、模型权限或额度一定可用。模型实验的错误会与离线结果分开记录；不要为了消除错误去关闭所有执行隔离。

## 下一步与常见失败

- 找不到 `python3`：先安装受支持的 Python，确认终端使用的是你刚安装的解释器。
- `codex` 不在 PATH：课程和离线实验仍可运行；安装 CLI 后重新运行 `probe`。
- 端口被占用：给 `serve` 换一个端口，例如 `--port 8767`。
- 搜索没有结果：确认用 HTTP 打开，尝试简短关键词，如 `MCP`、`approval` 或 `AGENTS`。
- 真实调用失败：保留退出码与错误类别，按[实验指南](labs.md)检查；不要将失败改标成通过。

环境就绪后，进入[第 1 章](01-first-task.md)。你的第一个学习产出应是一份可审查的代码改动，不是一段“模型说做完了”的文字。
