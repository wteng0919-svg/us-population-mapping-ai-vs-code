# 完整对比记录：方法、数字、时间线与局限

本文是 [README](../README.md) 的技术底稿。所有数字都可以用 `code/verify_join_quality.py` 从 `gadm41_USA_2.dbf` 与 `data/population_2025_counties.csv` 复算。

---

## 1. 问题定义

**输入**

- 人口：*Population by Age and Sex – US, States, Counties*，2025 年县级 3,145 行，合计 341,798,195 人；
- 边界：GADM 4.1 level 2，3,148 个面，51 个 `NAME_1`，EPSG:4326。

**输出**

1. 每个州一张人口热力图（A4、含制图要素）；
2. 一张全美图；
3. 一本 PDF 画册。

**约束**

- 两边没有共同主键（GADM 无 FIPS），只能按“州名 + 县名”连接；
- 一次性的探索型任务，不是要上生产的 ETL。

所以这不是“空间连接精度”的对比，而是：**在同一个名称匹配难题上，手写规则和 Agent 谁能把错误压得更低，并把制图做完。**

---

## 2. 环境

| 组件 | 第一 / 二轮 | 第三轮 |
|---|---|---|
| 运行环境 | WSL2 + Miniconda（`gis` env，Python 3.12） | Windows 11 + QGIS 4.2.3 |
| 数据访问 | PostGIS（`raw.USA_level2`，由 shapefile 导入） | QGIS 直接读 `gadm41_USA_2.shp` |
| 计算 | GeoPandas + pandas + Matplotlib | PyQGIS（由模型通过 `executeCode` 生成） |
| 渲染 | `fig.savefig(dpi=150)` | QGIS 布局导出（200 dpi，A4 横向） |
| 交互 | Jupyter Notebook，逐格改代码 | Cherry Studio，自然语言 |
| 模型 | — | DeepSeek API（`deepseek-flash`） |

第一轮把 GADM 导入了 PostGIS，用 `gpd.read_postgis()` 读；第二轮沿用。第三轮完全绕开数据库，直接读 shapefile。两轮的底图都是 **3,148 个要素**；Notebook 里第二轮的 `3,150` 是合并后的行数，多出的 2 行来自两个重复名称键，不是底图多了两个面。

---

## 3. 时间线

| 时间 | 事件 |
|---|---|
| 11-14 | 下载 GADM，导入 PostGIS；准备人口 CSV |
| 11-15 20:12 | 第一轮出图：48 张 PNG（`第一版/`），连续色带，3 个州整州缺失 |
| 11-15 20:44 | 第二轮出图：50 张 PNG，补清洗规则 + 分位数分级 |
| 11-17 ~ 11-18 | 安装 QGIS MCP 插件、`uvx` 拉起 MCP server、Cherry Studio 接通；期间多次返回 `null`，排查端口/插件/版本 |
| 11-18 22:58 | Agent 开始做属性挂接（3,114 → 3,120 → 3,119 → 3,123） |
| 11-18 23:13 | 51 张州图落盘 |
| 11-18 23:20 | 52 页 PDF 画册落盘 |

第三轮从“开始挂接”到“51 张图落盘”，文件时间戳跨度约 **15 分钟**；但这不是严格的耗时对比——第一轮之前我还花了两天搭 PostGIS/QGIS 环境，且两轮的任务范围不同（第一轮含建库，第三轮没有）。

---

## 4. 三轮的具体做法

### 4.1 基线（170 个未匹配）

```python
gdf["NAME_1"] = gdf["NAME_1"].str.upper()
gdf["NAME_2"] = gdf["NAME_2"].str.upper()
pop["County"] = pop["County"].str.upper().str.replace(" COUNTY", "", regex=False)
merged = gdf.merge(pop, left_on=["NAME_1", "NAME_2"], right_on=["State", "County"], how="left")
```

结果 2,978 / 3,148。失败集中在：

| 原因 | 数量（约） |
|---|---:|
| Louisiana `Parish` | 64 |
| Virginia `Independent City` | 38 |
| Alaska `Borough` / `Census Area` | 26 |
| Connecticut 旧县 | 8 |
| `De Kalb` / `Mc Kean` / `Ste.` 等 | 7 |
| 五大湖水面 | 11 |
| 其余零散（`St.`、城市后缀等） | 16 |

后果不只是数字：`if state_data["Population"].isna().all(): continue` 让**阿拉斯加、康涅狄格、路易斯安那**整州没有图。第一版的美国全图则因为阿留申群岛跨 180° 经线，被拉成 4.7:1 的细条，七成画布是空白。

### 4.2 规则清洗（66 个未匹配）

补了 6 类后缀与 3 组缩写，并把渲染改成分位数：

```python
for suffix in [" COUNTY", " PARISH", " BOROUGH", " CENSUS AREA", " CITY", " MUNICIPALITY"]:
    key = key.replace(suffix, "")
key = key.replace("ST. ", "SAINT ").replace("FT. ", "FORT ").replace("MT. ", "MOUNT ")
```

```python
state_data.plot(column="Population", cmap="Reds", scheme="Quantiles", k=5, ...)
```

结果 3,082 / 3,148（Notebook 按合并行数打印 3,084 / 3,150；多出的 2 行来自两个重复名称键）。康涅狄格仍然整州无图，因为 9 个 Planning Region 和 8 个旧县没有同名对应。

### 4.3 Agent（25 个未匹配）

模型的做法与 4.2 结构相同——写 Python、标准化名称、写字段——但多了三件事：

1. **二级索引**：先精确匹配，再“去掉所有空格”匹配，解决 `De Kalb`、`Mc Kean`；
2. **冲突检测**：同一个 GADM 面被两行 CSV 命中时（市/县同名），保留先到者并记录冲突，而不是静默覆盖；
3. **回读验证**：`getFieldStatistics` + 抽样 + 总和对比，发现异常后重跑。

它没有用 QGIS 的“连接”功能，也没有做空间连接，所以**匹配率的提升不是 QGIS 引擎的功劳**，而是规则更完整。

---

## 5. 误差分解

### 5.1 66 → 25

| 类别 | GeoPandas | Agent | 差异原因 |
|---|---:|---:|---|
| 五大湖水面（`Water body`） | 11 | 11 | 无法匹配，也不该匹配 |
| 康涅狄格旧县 | 8 | 8 | 行政口径变更 |
| 弗吉尼亚独立市 | 35 | 2 | Agent 去掉了 `Independent City` 后缀；剩 2 个是已撤销的 Bedford City / Clifton Forge City |
| 阿拉斯加旧普查区 | 5 | 4 | 别名/合并 |
| `De Kalb` | 4 | 0 | 去空格 |
| `Ste. Genevieve` | 1 | 0 | 缩写替换 |
| `Mc Kean` | 1 | 0 | 去空格 |
| `Shannon` → `Oglala Lakota` | 1 | 0 | 别名 |
| **合计** | **66** | **25** | **+41** |

### 5.2 25 个是什么

| 类别 | 数量 | 具体 |
|---|---:|---|
| 水面 | 11 | Lake Michigan（IL/IN/MI/WI）、Lake Superior（MI/MN/WI）、Lake Huron（MI）、Lake St. Clair（MI）、Lake Erie（OH）、Lake Ontario（NY） |
| 康涅狄格旧县 | 8 | Fairfield、Hartford、Litchfield、Middlesex、New Haven、New London、Tolland、Windham |
| 阿拉斯加旧区 | 4 | Prince of Wales-Outer Ketchikan、Skagway-Yakutat-Angoon、Valdez-Cordova、Wrangell-Petersburg |
| 弗吉尼亚旧市 | 2 | Bedford City（已并入县）、Clifton Forge City（已并入 Alleghany 县） |

剔除 11 个水面后，**真实数据缺口 14 个**，有效覆盖率 3,123 / 3,137 = **99.55%**。

### 5.3 那 482 万人的差额

| 来源 | 人口 |
|---|---:|
| 康涅狄格 9 个 Planning Region（GADM 无对应面） | 3,688,496 |
| 4 条市/县同名记录（Baltimore City、St. Louis City、Franklin City、Richmond City） | 1,093,876 |
| 阿拉斯加 4 个旧区 + 弗吉尼亚 2 个旧市等 | 约 38,000 |
| **合计** | **约 4,820,000** |

CSV 合计 341,798,195 − 图面合计 336,978,041 = **4,820,154**，可以对上。

> 注意：Baltimore City 与 St. Louis City 在 GADM 里没有独立市面，它们的 CSV 行被判定为“冲突”而不是“无匹配”，所以没有出现在 25 个空值面里。这是处理层面的“丢行”——模型在总结里点出来了，但字段里没有留标记，事后只能靠总和反推。这也是属性连接最危险的地方：如果不做总和校验，根本发现不了。

---

## 6. 制图规格（第三轮）

| 项目 | 规格 |
|---|---|
| 页面 | A4 横向 297×210 mm，200 dpi，2338×1653 px |
| 标题 | 中文州名 + “2025 年人口分布”，微软雅黑 19 pt 深蓝 |
| 副标题 | 英文州名 + 县级单元数 + 总人口 + 无数据数 |
| 分级 | 各州内部 7 级分位数；单元少的州降为 5 / 3 / 1 级；YlOrRd |
| 无数据 | 灰色 + 图例“无数据（水面或未匹配）” |
| 图例 | 千分位断点 + “本州县级分位数分级”说明 |
| 比例尺 | 左下角公里比例尺（自适应长度）+ 数值比例尺（每州不同） |
| 指北针 | 右上角 |
| 页脚 | 数据源 + 行政区源 |
| 命名 | `序号_州中文名_2025年人口分布.jpg`，字母序 |
| 全美图 | 本土主图 + 阿拉斯加/夏威夷插图，全国统一 7 级 |
| 画册 | 52 页（00 全美 + 01–51 州） |

阿拉斯加那张还处理了一个细节：排除跨 180° 经线的阿留申西端小岛对布局范围的影响，否则主图会被拉成一条线。

---

## 7. 这个对比不能证明什么

- **不是受控实验**：只有一个数据集、一次运行；模型版本、提示词、上下文都会影响结果；
- **没有测成本**：token 消耗、API 费用、失败重试次数都没有记录；
- **变量不干净**：第二轮同时改了“清洗规则”和“分级方式”，无法把匹配提升与视觉提升分开；
- **人工时间被低估**：第三轮看起来是“一句话”，但前期装 QGIS 插件、排查 MCP 返回 `null` 花了两天；这些工作不会因为换 Agent 而消失；
- **AI 的叙述会错**：本次它把 11 个水域说成 9 个，三类相加是 21 却写成“25 个（分 3 类）”；但另一方面，它主动列出了 4 条市/县同名记录并给出了处理选项。所有对外数字都应以字段统计为准。

---

## 8. 得到的经验

1. **属性连接的敌人是命名，不是几何。** 这次 90% 的误差来自 `Parish`、`Borough`、`Independent City`、空格、缩写、改名，而不是投影或空间谓词。
2. **匹配率要按“要素”和“人口”两个口径看。** 25 个空值面只占 0.8%，但背后是 482 万人；只报面数会低估问题。
3. **Agent 的价值是“迭代速度”，不是“一次做对”。** 它第一版也只有 3,114，靠的是自己查、自己改；人如果愿意写同样的四版代码，也能达到 3,123。
4. **制图规范是 QGIS 的存量优势。** 比例尺、指北针、图例、跨经线处理，在布局器里是现成的；模型把它们组合起来，比手写 Matplotlib 快得多。
5. **交付物必须能复核。** 所以这个仓库把 `.dbf` 里的 `POP_2025` 当作证据，把 `verify_join_quality.py` 当作验算器，而不是只放几张好看的图。
