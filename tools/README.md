# tools —— 构建脚本

## build_single_file.py

把 `docs/zh/` 的 00–13 章与 `reference/glossary.md` 合成一个自包含的单文件 HTML，
默认输出 `docs/zh/kubernetes-the-hard-way-zh.html`。生成结果已提交到仓库，可直接双击离线阅读。

### 依赖

- Python 3.10+
- `pip install markdown`
- 如需内嵌字体：`pip install fonttools brotli`

### 内嵌字体（默认开启）

脚本按文档**实际用到的字符**对下列字体做子集化，再以 WOFF2 + base64 内嵌，
因此即使目标机器没有安装这些字体也能正确显示：

| 用途 | 字体 | 典型文件名 |
| --- | --- | --- |
| sans | Inter（可变字体） | `InterVariable.ttf` |
| serif | Source Serif 4（可变字体） | `SourceSerif4-VariableFont_opsz,wght.ttf` |
| mono | New Computer Modern Mono 10 | `NewCMMono10-Regular.otf` / `NewCMMono10-Bold.otf` |
| 中文 | KingHwaOldSong-GB | `京華老宋体-GB.ttf` |

字体在 `FONT_DIRS`（默认 `C:\Windows\Fonts` 及用户字体目录）中按候选名查找；
找不到就跳过该字体、退回浏览器本机字体。用 `--no-fonts` 可完全关闭内嵌。

### 内置主题

生成的 HTML 在侧栏提供主题切换（用 `localStorage` 记忆选择）：

| id | 风格 |
| --- | --- |
| `claude` | 暖陶土（默认，Claude 文档风） |
| `paper` | 宣纸水墨（朱砂红 + 宋体标题） |
| `github` | 简洁白（GitHub Docs 风，浅色代码块） |
| `nord` | 冷蓝（Nord 配色，无衬线标题） |
| `solarized` | 米黄（Solarized Light，浅色代码块） |
| `gruvbox-dark` | 暗色（Gruvbox Dark） |

主题在脚本的 `THEMES` 中以「CSS 变量覆盖」定义；`claude` 的完整取值写在模板 `:root` 里，
其余主题只覆盖差异项。切换状态记在 `localStorage` 的 `kthw-theme` 键，也支持用
`?theme=<id>` 指定（如 `...zh.html?theme=nord`）。

### 用法

```bash
python tools/build_single_file.py                 # 生成默认路径（含内嵌字体）
python tools/build_single_file.py --out out.html  # 指定输出路径
python tools/build_single_file.py --no-fonts      # 不内嵌字体
```

### 说明

- 脚本只读取 `docs/zh/` 与 `reference/glossary.md`，不改动译文；请先更新译文再重新生成。
- 每章顶部的元数据注释会被剥离；章节内 `.md` 链接改写为页内锚点；
  `../../README.md` 等仓库链接改写为 GitHub 链接，避免单文件里出现死链。
- 内嵌字体会明显增大文件（当前约 1.3 MB），换取完全离线、跨机器一致的显示效果。
