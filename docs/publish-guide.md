# 从零发布到 GitHub（网页版，约 10 分钟）

这份指南写给第一次发 GitHub 的人。不需要 Git 命令，全部在浏览器里完成。

---

## 0. 发布前检查（1 分钟）

- [ ] 仓库里没有 API Key、密码、数据库连接串（本项目已清理）；
- [ ] 单个文件都小于 **25 MB**（GitHub 网页上传上限）；
- [ ] 文件总数不超过 **100**（本项目约 20 个）；
- [ ] `README.md` 里的图片路径都是相对路径（`figures/...`），不是本机绝对路径。

当前仓库大小约 13 MB，其中 `album/USA_2025_Population_Atlas.pdf` 约 10 MB，可以正常网页上传。

---

## 1. 建账号 / 登录

打开 [github.com](https://github.com)，用邮箱或手机号注册，完成验证后登录。

---

## 2. 新建仓库

1. 右上角 **`+` → New repository**；
2. **Repository name**：`us-population-mapping-ai-vs-code`（全小写、用连字符，最稳妥）；
3. **Description**：

   ```
   US county population mapping: GeoPandas pipeline vs an LLM agent driving QGIS over MCP (3,148 counties, 52-page atlas)
   ```

4. 选 **Public**；
5. **不要**勾 “Add a README file”“Add .gitignore”“Choose a license”——我们本地已经有这些文件，勾了会冲突；
6. 点 **Create repository**。

---

## 3. 上传文件

进入空仓库后，点页面上的 **uploading an existing file**（或绿色 **Add file → Upload files**）。

1. 打开本地文件夹 `us-population-mapping-ai-vs-code`；
2. **全选里面的内容**（`README.md`、`album`、`code`、`data`、`docs`、`figures`、`results`、`LICENSE` 等），一起拖进浏览器上传区；
3. 等文件列表全部出现（约 20 个文件、13 MB）；
4. 下方 **Commit changes** 的说明填：

   ```
   Add comparison: GeoPandas vs QGIS MCP agent for US county population mapping
   ```

5. 点 **Commit changes**。

> **拖文件夹失败怎么办？**
> 先拖 `README.md` 和 `LICENSE`，提交；再进去分别拖 `code/`、`figures/` 等子文件夹。GitHub 会保留文件夹结构。
> 如果浏览器不支持拖文件夹，就进入仓库 → **Add file → Upload files**，一次拖一个子文件夹里的文件，并在文件名框里手动保留路径（较麻烦，建议用 Chrome / Edge）。

上传完成后，首页应该能看到 README 的标题、两张对比图、表格。

---

## 4. 把仓库“装修”一下

### 4.1 About（右上角齿轮）

- Description：同上面的英文简介；
- Website：留空，或填你的博客；
- Topics（建议）：`gis` `qgis` `geopandas` `mcp` `deepseek` `cartography` `population` `python` `llm-agent` `spatial-join`

### 4.2 Social preview

`Settings → General → Social preview`，上传 `figures/01_texas_three_versions.png`。别人分享链接时会显示这张对比图。

### 4.3 置顶

回到个人主页，点仓库右侧的 **Pin**，把它固定在首页。

### 4.4 确认 License

仓库首页右侧应显示 **MIT license**。如果没有，检查 `LICENSE` 是否在根目录。

---

## 5. 可选：把 27.7 MB 的矢量原版 PDF 放上去

`album/` 里是压缩版（10 MB，适配网页上传）。如果你想要矢量原版：

**方式 A：Release（推荐，单文件可到 2 GB）**

1. 仓库右侧 **Releases → Create a new release**；
2. Tag 填 `v1.0`，标题 `v1.0 - first release`；
3. 把原版 PDF 拖到 **Attach binaries**；
4. Publish release。

**方式 B：Git LFS**（需要装 Git 和 Git LFS，不适合第一次发布）

---

## 6. 以后怎么更新

- **改文字**：直接在 GitHub 网页打开 `README.md` → 铅笔图标 → 改 → Commit；
- **换图**：`figures/` → 点文件 → 右上角删除/上传新文件；
- **批量改**：装 [GitHub Desktop](https://desktop.github.com/)，克隆仓库到本地，改完点 Commit → Push。比网页方便，也不需要记命令。

---

## 7. 发布后自检

- [ ] 首页 README 的图片能正常显示（不是破图）；
- [ ] 点进 `docs/publish-guide.md`、`docs/mcp-setup.md`，相对链接能跳转；
- [ ] `album/USA_2025_Population_Atlas.pdf` 能在线预览/下载；
- [ ] 在手机浏览器打开一次，确认排版没崩；
- [ ] 把链接发给自己，确认未登录也能访问（Public 仓库）。

---

## 8. 几个常见坑

| 现象 | 原因 | 解决 |
|---|---|---|
| 上传按钮灰色 / 报错 | 单文件 > 25 MB | 压缩，或用 Release / LFS |
| README 图片裂开 | 路径大小写不一致，或 `figures/` 没上传 | 检查路径与文件名完全一致 |
| 中文文件名变乱码 | 浏览器/系统编码问题 | 本项目图片名是英文，PDF 名是英文，不受影响 |
| 提交后没有 README 预览 | 文件不在根目录，或名字不是 `README.md` | 移到根目录、改大小写 |
| 仓库显示 “No license” | `LICENSE` 内容格式不对 | 用本仓库的文件，别改开头 |

---

## 9. 一句话建议

第一次发布，**先把“能点开、图能看、数字对”这三件事做好**，比追求花哨的徽章和动图重要得多。这个仓库的卖点是“可复核的对比”，不是模板。
