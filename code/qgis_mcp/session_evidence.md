# 会话证据（摘录）

> 来源：Cherry Studio 本地会话库（2026-11-18，模型 `deepseek::deepseek-flash`）。
> 为便于阅读，删除了重复的推理片段与超长代码，保留了数字、结论和原话；路径做了缩写（`<DATA>` = 作者本机数据目录）。

---

## 0. 环境

| 项目 | 值 |
|---|---|
| QGIS | 4.2.3-Belém do Pará |
| 工程 | `USA_Test.qgz`，CRS EPSG:3857，7 个图层 |
| 数据 | `gadm41_USA_2.shp`（3,148 要素，EPSG:4326） |
| MCP 端口 | `127.0.0.1:9876` |
| 客户端 | Cherry Studio，MCP over stdio |
| 模型 | DeepSeek API（`deepseek-flash`） |

---

## 1. 第一次挂接：3,114

第一步是看数据长什么样：

> 用户：将这个 `<DATA>\Population by Age and Sex - US, States, Counties.csv` 文件里面的 Total Population 列和这个图层的每个县进行匹配属性挂接，只要 2025 年的数据。

模型先读 CSV 结构，再统计名称后缀：

```text
total rows 83104
2025 rows 3197
county rows 2025: 3145
[('County', 2918), ('Parish', 64), ('City', 38), ('Borough', 27), ('Region', 9), ('Area', 3), ...]
```

然后写第一版匹配：

```text
gadm keys 3148
csv county rows 3144 dups ['Oglala Lakota, SD']
matched features 3114 unmatched csv 24 ambig 0
unmatched by state [('AK', 9), ('CT', 9), ('AL', 1), ('IL', 1), ('IN', 1), ('MO', 1), ('PA', 1), ('SD', 1)]
```

它自己的判断：

> 3114 matched out of 3144 CSV rows. Unmatched fixable:
> - DeKalb: GADM has 'De Kalb' -> normalize by removing spaces? Add candidate with spaces removed comparison.
> - McKean PA: GADM 'Mc Kean'? probably 'McKean' vs 'Mc Kean'.
> - Oglala Lakota SD: GADM has 'Shannon' (old name) — can't fix by name; could map alias manually.
> - AK 9: outdated GADM names — alias map possible.
> - CT 9: planning regions vs old counties — no mapping. Leave unmatched.

---

## 2. 第二版：3,120

加了“空格不敏感”的二级索引：

```text
CSV 2025 county rows: 3144 | matched features: 3120 | unmatched CSV rows: 18 | dup skipped: ['Oglala Lakota, SD']
attribute write ok: True features written: 3120
features without population: 28
```

校验统计量：

```text
{"count": 3120.0, "sum": 334895581.0, "mean": 107338.3, "min": 52.0, "max": 9694934.0}
```

抽查：

```text
Alabama | Autauga | POP_2025 = 61920.0
California | Los Angeles | POP_2025 = 9694934.0
New York | Kings | POP_2025 = 2653963.0
Texas | Harris | POP_2025 = 5045026.0
South Dakota | Shannon | POP_2025 = 13338.0
Illinois | De Kalb | POP_2025 = 101835.0
Pennsylvania | Mc Kean | POP_2025 = 38984.0
Virginia | Alexandria | POP_2025 = 160662.0
```

---

## 3. 它发现了一个人眼很难发现的 bug

> **推理摘录**：Note: GADM has Lake Michigan etc. (water areas as "counties") — those legitimately have no population.
> ...
> So 'Fairfax' is the county and 'Fairfax City' the city. CSV 'Fairfax Independent City' matched base 'fairfax' → wrong! It matched the county (Fairfax County, pop 1,148,000?), not the city (26,772).

问题在于：`Fairfax Independent City` 的标准化结果 `fairfax` 同时命中县和市，先写入县，市的数据就把县覆盖了。第三版加了“候选优先级 + 已占用检测”：

```text
write ok: True | features: 3119
unmatched CSV rows: 21
by state: [('AK', 9), ('CT', 9), ('VA', 2), ('NV', 1)]
city-vs-county conflicts: [('Baltimore City County, MD', 'Baltimore County, MD'),
                           ('St. Louis City County, MO', 'St. Louis County, MO'),
                           ('Franklin  Independent City, VA', 'Franklin County, VA'),
                           ('Richmond  Independent City, VA', 'Richmond County, VA')]
sum POP_2025: 336821589.0
```

注意它把 `Richmond` 县的值打印成了 `9294.0`——这是 Richmond County 的真实值，不是 Richmond City 的 237,257。市的数据被正确地“让”出来了。

---

## 4. 第四版：3,123

最后一轮修了两个 bug：`strip_type()` 同时删多个后缀，把 `Charles City County` 变成了 `charles`；以及补了别名。最终：

> 属性挂接已完成 ✅
>
> **匹配结果**
> - 图层共 3,148 个要素
> - 成功写入：**3,123** 个（99.2%）
> - 未匹配：25 个
> - 校验：洛杉矶县 9,694,934、哈里斯县 5,045,026、Kings(NY) 2,653,963、Alexandria city 160,662 —— 均与 CSV 一致
> - 合计 3.3698 亿，与 CSV 全美 2025 年 3.4178 亿相差约 480 万，差异来源见下

它给出的分类里有**两处算术问题**：

> **未匹配的 25 个要素（分 3 类，属数据源版本差异，不是匹配错误）**
> 1. **9 个五大湖水面多边形**（Michigan/Illinois/Wisconsin/Minnesota/New York/Ohio/Indiana 的 ...）
> 2. **8 个康涅狄格州旧县** ...
> 3. **4 个阿拉斯加旧人口普查区** ...

实际按 `.dbf` 复核：`TYPE_2 = Water body` 的要素是 **11 个**（6 个湖，跨 7 个州），不是 9 个；而且 9 + 8 + 4 = **21**，不是 25——它漏掉了 2 个弗吉尼亚旧市（Bedford City、Clifton Forge City）。图标题“25 个无数据”是对的，错在文字总结。

**但它主动暴露了另一类问题**，这一点值得肯定：

> **另有两处结构差异需你确认**
> - **马里兰 Baltimore City**（CSV 记作 "Baltimore City County"）与 **密苏里 St. Louis City**（"St. Louis City County"）：GADM 中这两个市与该县是**同一个要素**，现在字段里只有县的值（847,650 / 990,911）。若该多边形实际覆盖市县全域，我可以在 2025 年人口里把市人口加进去。
> - **弗吉尼亚 Franklin / Richmond 独立市**：GADM 无独立市要素，已保证县要素取到县的值（Richmond 9,294），独立的市记录留空。
>
> 接下来要我做哪一项？
> 1. 把 Baltimore City / St. Louis City 人口并入对应要素
> 2. 用面积加权把 CT 的 9 个 Planning Region 人口分摊到 8 个旧县（估算值，会标注字段名）
> 3. 过滤掉 9 个湖泊多边形，或给它们单独样式
> 4. 保存工程

没有静默处理，也没有替用户拍板——这是它做得比“自动化脚本”更好的地方。但它同样没有量化这 4 条记录到底带走了多少人口（约 109 万），这部分需要人回读 CSV 补上。

---

## 5. 制图：一次对话，62 次工具调用

> 用户：按照各州输出每个州的人口分布热力图，做好比例尺，图例，指北针，标题，命好好字，新建一个文件夹，给我放在桌面上，格式为JPEG

> 已全部输出完成 ✅
>
> 共 **51** 个 JPEG 文件（50 州 + 哥伦比亚特区），合计 9.6 MB
>
> 每张图（A4 横向，200 dpi，2338 × 1653 px）：
> - 标题：州中文名 + "2025 年人口分布"
> - 副标题：英文州名 + 中文名 ｜ 县级单元数 ｜ 2025 年总人口 ｜ 无数据单元数
> - 热力图例：7 级（县少的州自动降为 5 / 3 / 1 级），YlOrRd，带千分位，附"无数据"灰块
> - 指北针：右上角；比例尺：左下角 + 数值比例尺（每州不同）
> - 数据来源脚注
>
> 处理细节：
> - 分级采用**各州内部的县级分位数**（否则全国统一分级下小州几乎全是一个颜色）
> - 阿拉斯加已排除跨 180° 经线的阿留申西端小岛对范围的影响
> - 导出后自动删除临时布局

然后它主动问了下一步：

> 需要我再补一份**多页 PDF 合集**或**全国总图**放进同一文件夹吗？另外工程目前尚未保存，需要我保存吗？

全美图和 52 页画册就是顺着这句话做出来的。

---

## 6. 可以复核的硬指标

| 指标 | 值 | 复核方式 |
|---|---:|---|
| GADM 要素 | 3,148 | `gadm41_USA_2.dbf` 记录数 |
| CSV 2025 县级行 | 3,145 | 过滤 `Year=2025 & Countyfips>0` |
| 写入 `POP_2025` | 3,123 | 字段非空计数 |
| 未匹配 | 25 | 字段为空计数 |
| 全美合计 | 336,978,041 | `SUM(POP_2025)`，与图标题一致 |
| 水面多边形 | 11 | `TYPE_2='Water body'` |

运行 `code/verify_join_quality.py` 可以在几秒内复现整张表。
