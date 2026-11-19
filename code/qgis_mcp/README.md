# QGIS MCP 这一轮：工具与调用方式

## 架构

```
Cherry Studio（DeepSeek API）
   │   MCP over stdio
   ▼
qgis-mcp server（Python，uvx 启动）
   │   TCP socket 127.0.0.1:9876
   ▼
QGIS MCP plugin（运行在 QGIS 进程内）
   ▼
PyQGIS / QGIS Processing / 布局引擎
```

模型没有“看屏幕”，也没有点菜单。它拿到的是工具返回的 JSON（图层、字段、统计量、截图），然后写 PyQGIS 代码执行。

## 本次实际用到的 16 个工具

| 工具（Cherry Studio 显示名） | 调用次数 | 用途 |
|---|---:|---|
| `executeCode` | 66 | 读 CSV、名称标准化、写 `POP_2025` 字段、建布局、设样式、导出 |
| `getCanvasScreenshot` | 8 | 看当前画布（地图长什么样） |
| `ping` | 7 | 连通性 |
| `getQgisInfo` / `getProjectInfo` / `getLayers` | 6 / 6 / 6 | 环境与图层清单 |
| `renderMap` | 6 | 渲染预览 |
| `setCanvasExtent` | 4 | 缩放到州 / 全国范围 |
| `getLayerFeatures` | 3 | 抽样检查名称 |
| `addVectorLayer` / `zoomToLayer` | 1 / 1 | 加载 GADM shapefile |
| `createCheckpoint` | 1 | 写字段前存档 |
| `getFieldStatistics` | 1 | 校验 `POP_2025` 总数、极值 |
| `setLayerStyle` / `setLayerVisibility` | 1 / 1 | 分级设色、隐藏干扰图层 |

合计 **119 次调用**（整场会话，含插件排障）。其中“51 张州图”那一轮，模型在一条回复里连续发起了 **62 次**工具调用。

> 关于“125 个工具”：Cherry Studio 的工具面板显示该 MCP 服务器注册了 125 个工具；上面 16 个是本次任务真正调用到的。不同 fork / 版本的 `qgis-mcp` 工具数量差别很大（上游 [jjsantos01/qgis-mcp](https://github.com/jjsantos01/qgis-mcp) 的基础版本只有 15 个），以你本地客户端显示为准。

## 为什么它比 GeoPandas 多匹配 41 个

不是 QGIS 的空间引擎更准——这次根本没有做空间连接，做的是**属性连接**。真正的差别是模型把名称规则写得更完整，并且会回读统计量验证：

1. 第一版：小写 + 去标点 + 去类型后缀 → 3,114
2. 加“去空格比较”解决 `De Kalb` / `Mc Kean` → 3,120
3. 发现 `Fairfax Independent City` 被写进 `Fairfax` 县（同名覆盖），改成“市/县候选优先 + 已占用检测” → 3,119
4. 修正 `Charles City` / `James City` 被误判为“市”的 bug，补 `Oglala Lakota → Shannon` 别名 → **3,123**

完整摘录见 [session_evidence.md](session_evidence.md)。

## 文件

- [`prompts.md`](prompts.md)：实际输入的自然语言指令（含全美图 / 画册的复现用提示词）
- [`session_evidence.md`](session_evidence.md)：会话中的关键片段与数字
- 环境配置：[`../../docs/mcp-setup.md`](../../docs/mcp-setup.md)
