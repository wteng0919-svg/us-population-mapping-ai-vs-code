# 数据说明

## 仓库里有什么

| 文件 | 说明 |
|---|---|
| `population_2025_counties.csv` | 2025 年县级人口切片，3,145 行，来自原始表 *Population by Age and Sex – US, States, Counties* |

字段：

| 字段 | 示例 | 说明 |
|---|---|---|
| `Description` | `Autauga County, AL` | 原始描述，"县名, 州缩写" |
| `Statefips` | `01` | 州 FIPS |
| `Countyfips` | `001` | 县 FIPS（州内唯一，**不能跨州直接连接**） |
| `Year` | `2025` | 年份 |
| `Total Population` | `61920` | 总人口 |

原始表共 83,104 行（2000–2025，每年 3,197 行 = 1 个全国行 + 51 个州行 + 3,145 个县行）。本仓库只保留 2025 年、`Countyfips > 0` 的县级记录，用于复现匹配率；完整表请向原数据提供方获取。

> 原始文件没有附带许可说明。仓库仅保留复现所需的最小切片；如果原提供方有转载限制，请以原说明为准。

## 仓库里没有什么

**GADM 边界没有入库。** `gadm41_USA_2.shp` 单文件 33–42 MB，超过 GitHub 网页单文件 25 MB 的上限，而且 GADM 有自己的许可要求。

请从 [gadm.org](https://gadm.org/download_country.html) 下载 **USA / Level 2 / Shapefile**（本项目使用 GADM 4.1），解压后得到：

```
gadm41_USA_0.shp   # 国界
gadm41_USA_1.shp   # 州界（51 个）
gadm41_USA_2.shp   # 县界（3,148 个要素）
```

复现脚本只需要 `gadm41_USA_2.shp` 及其同名 `.dbf / .shx / .prj / .cpg`。

## 数据质量：三个必须先知道的事实

1. **没有共同主键。** GADM 只有 `NAME_1`（州名）和 `NAME_2`（县名），没有 FIPS；CSV 的 `Countyfips` 是州内编号。所以只能按“州名 + 县名”连接，名称标准化是主要工作量。
2. **两套行政口径不一致。** 2025 年康涅狄格州已改为 9 个 Planning Region，GADM 仍是旧 8 县；阿拉斯加有多个普查区合并/改名；弗吉尼亚的独立市在 2020 年后也有撤并。这类差异**不是匹配算法能解决的**。
3. **GADM 里有 11 个水面多边形。** 它们 `TYPE_2 = Water body`（Lake Michigan、Lake Superior、Lake Huron、Lake Erie、Lake Ontario、Lake St. Clair），不是县，CSV 中自然没有人口。制图时应显式标为“无数据”，而不是当成 0。

另外，2025 年切片中 `Oglala Lakota, SD` 出现两行（FIPS 46-102）且数值相同，匹配时需去重。

## 许可

- GADM 4.1：见 [GADM license](https://gadm.org/license.html)（可免费用于非商业用途，需署名，不得再分发原始数据）；
- 人口数据：版权归原提供方，本仓库仅作复现用途；
- 本仓库生成的地图与画册：[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。
