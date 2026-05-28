# DOCX 渲染预览格式闭环

这个流程不是为了单独做最终 QA，而是服务于一本通生成本身：每次程序生成 DOCX 后，立刻在 Linux headless 环境中把 DOCX 渲染成 PDF 和页面图片，让 Codex 看到接近 Word/WPS 打开后的真实分页效果，再反向修改 DOCX 生成逻辑。核心目标是减少“内容理解正确，但写进 Word 后目录、标题、Tips、表格、图片、跨页、空白等格式出问题”的情况。

## 环境依赖

推荐在 Codex Linux session 安装：

```bash
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  libreoffice-writer libreoffice-core libreoffice-common \
  fonts-noto-cjk poppler-utils
```

依赖作用：

- `libreoffice` / `soffice`：headless DOCX -> PDF 渲染。
- `fonts-noto-cjk`：降低中文字体缺失导致的换行、溢出、乱码风险。
- `pdfinfo`：读取 PDF 页数和页面尺寸。
- `pdftoppm`：导出页面预览图。
- `pdftotext`：辅助发现空白页、文字异常少的页面。

## 生成闭环

每次一本通 DOCX 生成后，先跑：

```bash
python3 scripts/docx_format_preview.py path/to/input.docx \
  --out-dir format-preview/docx-render/<项目名> \
  --force
```

然后按 `format_report.md`、`output.pdf` 和联系表回看格式问题，修改 DOCX 生成脚本或样式设置，再重新生成 DOCX 并重复渲染。只有当渲染预览里看不到明显格式问题时，才进入交付或人工复核。

已确认的渲染边界：LibreOffice 导出的 PDF 与 Word/WPS 基本接近，字体有轻微差异可以接受；但 Word 里的 Tips logo/VML 旋转装饰可能无法完全还原，尤其是蝴蝶结里的 `铁头tips` 斜放文字。这个局部以 Word/WPS 打开效果为准：如果 Word/WPS 中 `铁头tips` 正常斜着展示在蝴蝶结里，而 PDF 中该装饰不一致，不要据此修改 DOCX 生成逻辑。

## 标准输出

输出目录包含：

- `output.docx`：待交付 DOCX 的复制件。
- `output.pdf`：LibreOffice 渲染出来的 PDF。
- `previews/page-*.png`：每一页的页面预览图。
- `contact-sheet-*.png`：页面联系表，方便快速扫版式。
- `format_report.md`：格式风险提示、生成器修复重点和文件清单。
- `output.txt`：从 PDF 抽取的文本，仅作诊断辅助。

## 格式报告必须写清楚

`format_report.md` 至少要包含：

- 输入 DOCX、输出目录、生成时间、预览 DPI。
- `output.docx`、`output.pdf`、预览图、联系表的位置。
- LibreOffice、Poppler 命令是否成功。
- PDF 页数、页面尺寸，是否接近 A4 纵向。
- 是否存在疑似空白页或文字很少的页面。
- DOCX 中是否检测到 Heading 1/2/3、TOC 目录域、表格、图片、分页符。
- 标题/目录/超链接样式是否疑似非黑色。
- 生成器下一轮需要重点修复的问题。

## 生成器修复重点

每轮生成后，先看 PDF 和联系表，重点判断这些问题是否需要回改生成逻辑：

- 目录是否像 Word/WPS 自动生成目录，是否有蓝色标题或蓝色目录文字。
- 章节标题、二级标题、三级标题是否套用了正确标题样式，标题是否孤立在页尾。
- Tips logo 是否和底框在同一页，Tips、补充内容、表格、图片是否被截断跨页。Tips 蝴蝶结里的斜放 `铁头tips` 装饰以 Word/WPS 为准，PDF 只辅助检查位置和分页。
- 是否出现大块空白；如果由图片比例导致，优先重画或调整图片比例，不要用硬分页制造更大的空白。
- 图表在 A4 黑白打印下是否清晰，不能依赖颜色区分信息。
- 页码是否从正文第一页开始，封面和目录是否未计入正文页码。

## 进入交付前的最低标准

这个流程不保证 Microsoft Word/WPS 里百分百一致，但能让 Codex 在生成阶段先修掉大部分低级格式问题。满足以下条件才进入交付或人工复核：

- `format_report.md` 中没有 `ERROR`。
- `RISK` 项已经看过，能明确是不影响成品的提示，或已经通过回改生成逻辑处理。
- PDF 和联系表已扫过，未发现标题跨页、Tips/表格截断、目录异常、大块空白、图片文字看不清等问题；Tips 蝴蝶结/旋转文字若只在 PDF 中失真，但 Word/WPS 正常，可记录为 LibreOffice 渲染差异。
- 如果发现问题，先改 DOCX 生成逻辑，再重新跑门禁；不要只改 PDF 或预览图。

## 局限

- LibreOffice 的渲染和 Microsoft Word/WPS 不会完全一致，但能提前暴露大部分分页、字体、目录、图片、表格和空白问题。
- 已知差异：LibreOffice PDF 可能不能完全还原 Word/WPS 中 Tips logo 的蝴蝶结形状、文本框旋转和斜放 `铁头tips`。这类装饰性元素以 Word/WPS 版为准。
- 标题孤立页尾、Tips 被切开、图表可读性等问题仍需要看 PDF/预览图判断。
- 对长文档会生成很多 PNG，最终交付给主管时可只发送 DOCX、PDF、`format_report.md` 和联系表；完整 `previews/` 留在本地或压缩后按需发送。
