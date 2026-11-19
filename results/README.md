# 结果文件说明

全部结果都可以用 [`../code/verify_join_quality.py`](../code/verify_join_quality.py) 从
`gadm41_USA_2.dbf` + `../data/population_2025_counties.csv` 复算。

| 文件 | 内容 |
|---|---|
| `join_summary.json` | 三个口径的汇总数字（要素数、匹配数、未匹配数、人口合计） |
| `unmatched_baseline.csv` | 基线（只去 `County` + 转大写）未匹配的 170 个要素 |
| `unmatched_geopandas.csv` | 规则清洗后仍未匹配的 66 个要素 |
| `unmatched_qgis.csv` | Agent 跑完后 `POP_2025` 仍为空的 25 个要素，附 `reason` |

字段：`GID_2`（GADM 要素 ID）、`NAME_1`（州）、`NAME_2`（县）、`TYPE_2`（GADM 类型）。

## 读这几个 CSV 时注意

1. **25 个不等于 25 个“县”。** 其中 11 个是 `TYPE_2 = Water body` 的湖面多边形，8 个是康涅狄格旧县，4 个是阿拉斯加旧普查区，2 个是已撤销的弗吉尼亚市。
2. **66 个里有 35 个是弗吉尼亚独立市**，因为第二轮的 `clean_name()` 没有处理 `Independent City` 后缀。这不是“数据错”，是规则没覆盖。
3. **未匹配的“面”与未落位的“行”不是一回事。** Agent 还把 4 条市/县同名记录判为冲突（Baltimore City、St. Louis City、Franklin City、Richmond City），这些县面本身有值，但市的人口没有进入图面（约 109 万人）。详见 [../docs/comparison.md](../docs/comparison.md) 第 5.3 节。

## 重新生成

```bash
python code/verify_join_quality.py \
  --gadm-dbf /path/to/gadm41_USA_2.dbf \
  --population-csv data/population_2025_counties.csv \
  --dump-dir results
```
