# 原始 Notebook（保留当时的运行输出）

- `01_geopandas_original_session.ipynb`：第一轮 + 第二轮的真实 Notebook，包含 `3,084 / 3,150` 的打印结果、18 个整州缺失列表，以及导出 GeoJSON 的单元格；
- `02_second_edition.ipynb`：把清洗规则抽成 `clean_name()` 后的“重生版”。

这两个文件是**历史记录**，路径已经替换为占位符（`/path/to/data`、`/path/to/output`），数据库连接里的账号密码也已移除。直接运行需要改回你自己的路径，或者用上一级目录里参数化的脚本。

参数化、可直接运行的版本在上一级目录：

- [`01_baseline_naive_join.py`](../01_baseline_naive_join.py)
- [`02_cleaned_pipeline.py`](../02_cleaned_pipeline.py)
