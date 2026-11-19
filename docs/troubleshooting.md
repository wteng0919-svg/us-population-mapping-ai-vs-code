# 运行失败排查

先确认你运行的是哪一个文件。下面按“最可能遇到的错误原文”组织，直接搜报错关键字即可。

---

## 1. `python` 没反应 / 弹出 Microsoft Store

Windows 自带的“应用执行别名”把 `python` 指向了商店。

- 装 [Python 3.11+](https://www.python.org/downloads/)，安装时勾选 **Add python.exe to PATH**；
- 或者用 `py -3` 代替 `python`；
- 本仓库的 `run_check.cmd` 会自动优先用 `py -3`。

验证：

```bat
py -3 --version
```

---

## 2. `ModuleNotFoundError: No module named 'geopandas'`

`code/verify_join_quality.py` **不需要** geopandas；只有 `code/geopandas/*.py` 需要。

```bash
conda create -n gis python=3.12 -y
conda activate gis
conda install -c conda-forge geopandas matplotlib mapclassify -y
```

`mapclassify` 必须装：`scheme="Quantiles"` 依赖它，否则会报 `ImportError: mapclassify` 或 `ValueError: Invalid scheme`。

---

## 3. `error: the following arguments are required: --gadm-dbf, --population-csv`

旧版本的脚本强制要求参数；现在的版本已经支持自动查找：

```bash
python code/verify_join_quality.py
```

它会依次找：

```
data/gadm41_USA_2.dbf
./data/gadm41_USA_2.dbf
./gadm41_USA_2.dbf
data/population_2025_counties.csv
```

找不到时会打印下载说明并退出（退出码 2），**不会抛一堆 traceback**。

---

## 4. `找不到数据文件` / `FileNotFoundError: data/gadm41_USA_2.dbf`

仓库**没有**收录 GADM 边界（单文件 33–42 MB，且有许可限制）。需要你自己下载：

1. 打开 <https://gadm.org/download_country.html>；
2. 选 **USA → Level 2 → Shapefile**；
3. 解压，把 `gadm41_USA_2.dbf`（以及同名 `.shp / .shx / .prj / .cpg`）放进 `data/`。

注意：`.dbf` 只是属性表，单独跑匹配率够用；要画图必须同时有 `.shp / .shx / .prj`。

---

## 5. `[!] No POP_2025 field` / 第三行显示 3148 matched

说明你用的是**原始 GADM 的 dbf**，不是 QGIS 会话跑完后的版本。`POP_2025` 是 Agent 写进去的字段，原始文件当然没有。

两种处理：

- 只看前两行（baseline / cleaned），第三行忽略；
- 或者按 [docs/mcp-setup.md](mcp-setup.md) 复现 Agent 那一轮，把 `POP_2025` 写回 shapefile。

脚本不会因此崩溃，只会在 stderr 提示。

---

## 6. `UnicodeEncodeError: 'gbk' codec can't encode character ...`

老版本 Python + 中文 Windows 控制台。临时解决：

```bat
set PYTHONIOENCODING=utf-8
chcp 65001
python code/verify_join_quality.py
```

或者直接在 Windows Terminal / VS Code 终端里跑。

---

## 7. `KeyError: 'Description'` / 列名带 `\ufeff`

CSV 带 BOM。仓库里的脚本已经用 `encoding="utf-8-sig"` 读取；如果你自己写了读取代码，记得加这个参数：

```python
pd.read_csv(path, encoding="utf-8-sig")
```

---

## 8. Notebook 一运行就报路径错误

`code/geopandas/notebooks/` 是**历史记录**，路径已脱敏成 `/path/to/data`、`/path/to/output`，数据库口令也被移除。它不是开箱即用的。

请用参数化脚本：

```bash
python code/geopandas/01_baseline_naive_join.py --gadm data/gadm41_USA_2.shp --pop data/population_2025_counties.csv --out outputs/baseline
```

---

## 9. `DriverError` / `Unable to open ... .shp`

- 缺 `.shx` / `.prj`：shapefile 是多个文件一套，不能只拷 `.shp`；
- 路径含中文/空格：Windows 上一般没事，但 WSL 里要注意 `/mnt/d/...` 的挂载；
- 压缩包没解压：`gadm41_USA_shp.zip` 不能直接读。

---

## 10. 画图很慢 / 内存爆

全国 3,148 个面不算大，慢通常是：

- `dpi=300` + `bbox_inches="tight"` 同时开；
- 在 Jupyter 里反复 `plt.show()` 不关图；
- 用 `scheme="Quantiles"` 对整国做分级（先按州分组再画会快很多）。

---

## 11. GitHub 上传失败：`Yowza, that's a big file!`

单文件超过 25 MB。本仓库的 PDF 已压到约 10 MB；如果你要传 27.7 MB 的矢量原版：

- 用 **Release** 附加大文件（单文件可到 2 GB），或
- 用 Git LFS。

详见 [publish-guide.md](publish-guide.md) 第 5 节。

---

## 12. MCP 工具全部返回 `null`

和 Python 脚本无关，是 QGIS 插件/MCP 连接问题。见 [mcp-setup.md](mcp-setup.md) 第 7 节：先确认插件 Start Server、9876 端口在监听、没有两个客户端同时连。

---

## 还是失败？

把这三样发给我/发到 Issue：

1. 你运行的**完整命令**；
2. 报错的**最后 20 行**（不是截图，文本更好搜）；
3. `python --version` 和 `conda list | findstr geopandas` 的输出。

绝大多数问题都能从这三样里定位。
