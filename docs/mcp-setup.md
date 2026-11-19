# QGIS + MCP + Cherry Studio 配置（Windows）

这套配置让大模型通过 MCP 直接操作本机的 QGIS：读图层、跑 PyQGIS、导出地图。全程本地，只有模型推理走 DeepSeek API。

> 本文按 2026-11 的实际环境整理（QGIS 4.2.3 + Windows 11 + Cherry Studio）。不同版本的路径/插件名可能变化，以官方 README 为准。

---

## 1. 架构

```
Cherry Studio ──(stdio)──▶ qgis-mcp server ──(TCP 127.0.0.1:9876)──▶ QGIS 插件 ──▶ PyQGIS
```

- **QGIS 插件**：在 QGIS 进程内开一个 socket 服务（默认 9876），执行收到的命令；
- **MCP server**：把 MCP 协议翻译成上面的 socket 命令，通常由客户端自动拉起；
- **客户端**：Cherry Studio 通过 stdio 启动 server，把工具列表交给模型。

---

## 2. 前置条件

| 组件 | 说明 |
|---|---|
| QGIS | 3.x 以上；本项目用 4.2.3 |
| uv / uvx | [安装说明](https://docs.astral.sh/uv/getting-started/installation/)；Windows：`powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"` |
| Cherry Studio | 支持 MCP 的版本 |
| DeepSeek API Key | 在 Cherry Studio 的模型服务里配置 |

---

## 3. 安装 QGIS 插件

1. 下载 [qgis-mcp](https://github.com/jjsantos01/qgis-mcp) 源码（或 `git clone`）；
2. 把 `qgis_mcp_plugin/` 整个文件夹复制到 QGIS 的插件目录：

   ```
   C:\Users\<你>\AppData\Roaming\QGIS\QGIS4\profiles\default\python\plugins\
   ```

   路径可以在 QGIS 里确认：`设置 → 用户配置 → 打开当前配置文件夹`，再进 `python\plugins`；

3. 重启 QGIS → `插件 → 管理和安装插件 → 全部` → 搜索 “QGIS MCP” → 勾选；
4. 菜单 `插件 → QGIS MCP → QGIS MCP`，点 **Start Server**。

> 端口被占用时，先看 `netstat -ano | findstr 9876`，把占用进程找出来。

---

## 4. 配置 MCP server（Cherry Studio）

### 4.1 本项目实际使用的配置（uvx，直接从 GitHub 拉）

```json
{
  "mcpServers": {
    "qgis": {
      "command": "uvx",
      "args": [
        "--from",
        "https://github.com/nkarasiak/qgis-mcp/archive/refs/heads/main.zip",
        "qgis-mcp-server"
      ]
    }
  }
}
```

在 Cherry Studio：`设置 → MCP 服务器 → 添加 → 类型 stdio`，把 command / args 填进去，保存并启用。

### 4.2 本地源码方式（便于改代码/锁定版本）

```json
{
  "mcpServers": {
    "qgis": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\<你>\\qgis_mcp\\src\\qgis_mcp",
        "run",
        "qgis_mcp_server.py"
      ]
    }
  }
}
```

### 4.3 客户端里的模型

在 Cherry Studio 中把该 MCP 服务器绑定到使用 **DeepSeek API** 的助手/模型即可。本项目会话里模型显示为 `deepseek-flash`。

---

## 5. 验证

1. QGIS 插件已 Start Server；
2. PowerShell：`netstat -ano | findstr 9876` 应看到 `LISTENING`；
3. 在 Cherry Studio 里发：

   ```text
   调用ping
   ```

   返回 `{"pong": true}` 即通；
4. 再发 `调用get_project_info`，应返回工程路径、CRS、图层列表。

---

## 6. 工具清单

上游基础版（[jjsantos01/qgis-mcp](https://github.com/jjsantos01/qgis-mcp)）提供 15 个工具：

`ping`、`get_qgis_info`、`load_project`、`create_new_project`、`get_project_info`、`add_vector_layer`、`add_raster_layer`、`get_layers`、`remove_layer`、`zoom_to_layer`、`get_layer_features`、`execute_processing`、`save_project`、`render_map`、`execute_code`。

本项目实际使用的 fork 还包含 `getCanvasScreenshot`、`setLayerStyle`、`setLayerVisibility`、`setCanvasExtent`、`createCheckpoint`、`getFieldStatistics` 等（见 [../code/qgis_mcp/README.md](../code/qgis_mcp/README.md)）。Cherry Studio 工具面板显示该服务器注册了 **125 个工具**；本次任务实际调用 16 个。

> 工具数量取决于你装的 fork/版本，不必追求数字；真正关键的是 `execute_code`。

---

## 7. 常见问题

### 7.1 所有工具都返回 `null`

这是最常见的问题。按顺序排查：

1. QGIS 里插件是不是真的 **Start Server** 了（不是只打开面板）；
2. 端口是不是 9876：`netstat -ano | findstr 9876`；
3. **是不是同时开了两个客户端/两次连接**。插件是单连接模型，旧连接没断时，新请求会拿到空值；
4. 重启顺序：关掉 Cherry Studio 的 MCP 连接 → QGIS 里 Stop Server → Start Server → 重连；
5. 看 QGIS 的 MCP 日志：日志里会打印 `Executing: xxx`、`Connected to client`、`Client disconnected`。

### 7.2 插件版本与 server 版本不一致

日志可能提示：

```text
MCP server 0.99-probe connected, but this plugin is 0.15.3.
Not fatal: tools added since the older half was built will be missing or refused.
```

含义：server 比插件新，新增工具不可用。解决：让两边的仓库/分支版本对齐（都更新到同一 commit），或者只用双方都有的工具。

### 7.3 `Message too large: 2065855609 bytes`

渲染/返回的图片太大，超过传输上限。处理：

- 降低 `renderMap` 的宽高（例如 900×600）；
- 不要一次返回整张高分辨率图；
- 导出图片改用 PyQGIS 写到磁盘，再读文件，而不是把 base64 塞进返回值。

### 7.4 中文路径 / 空格

Windows 路径里有空格或中文时，PyQGIS 一般能处理，但 `addVectorLayer` 的 URI 需要正确转义。建议把数据放在纯英文、无空格的目录（例如 `D:\USA-data\`）。

### 7.5 安全性

- 插件启动时会提示 `Token authentication disabled (open)`：**只监听 127.0.0.1，不要映射到公网**；
- `execute_code` 会在 QGIS 进程里执行任意 Python，等价于本机代码执行权限；只连自己信任的客户端；
- 不要把 API Key 写进仓库；`fix_qgis_mcp_config.py` 这类改本地数据库的脚本只适合个人机器。

---

## 8. 参考

- [qgis-mcp（上游）](https://github.com/jjsantos01/qgis-mcp)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Cherry Studio](https://cherry-ai.com/)
