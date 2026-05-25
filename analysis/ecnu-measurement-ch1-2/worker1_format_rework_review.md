# 华东测量第1-2章格式返工检查清单

## 检视范围

- 已读分支内 `skills/tietou-yibentong-compilation/SKILL.md` 与 `skills/tietou-yibentong-compilation/references/requirements.md`。
- 已检视 `scripts/generate_ecnu_measurement_ch1_2.py`、当前 DOCX `deliverables/ecnu-measurement-ch1-2/华东347测量心理学一本通_第1-2章_自检版.docx` 的 XML/metadata。
- 本次只做格式返工审查与实现建议，不修改生成脚本和 DOCX 正文。
- 未使用 HF 一本通作为内容来源；仓库内未找到 `27深大普心一本通（最新版）(1).docx`，因此本建议按分支内格式规则落地，精确 logo/标签尺寸仍需以管理端可提供的样张复核。

## 当前主要发现

| 模块 | 发现 | 证据 | 影响 |
| --- | --- | --- | --- |
| A4 页面 | 当前 DOCX 不是 A4，而是 Letter 尺寸。脚本只设置页边距，未设置 `page_width/page_height`。 | `section.page_width=21.59cm`, `page_height=27.94cm`；脚本约 192-196 行只设 margin。 | 黑白打印、页尾分页、表格宽度判断都会失真；审核表中“A4黑白打印”结论不成立。 |
| Tips 样式 | `add_tip()` 用 1x1 外层表格承载 Tips，灰底黑框；标签只是正文行 `铁头Tips：标题`，没有独立 logo/标签区，也未按规则使用可见 `铁头tips` 标签。标题左对齐，未做“有标题时加粗居中”。 | 脚本约 110-165 行；XML 中 Tips 是普通表格，填充 `F2F2F2`，单线边框。 | 与样张式 Tips 视觉差距较大；黑白打印时层级不够清楚；用户投诉的 logo/边框/底色/字体无法通过当前 helper 统一修。 |
| Tips 跨页 | Tips 外层表格、标签段落、内部段落均无 keep 控制；只在前后插空段落。 | DOCX XML 未检出 `keepNext/keepLines/cantSplit`；表格行无 `cantSplit`。 | Tips 可能在页底被拆开，或标签留在上一页、正文到下一页。 |
| 表格格式 | 表格均为 `Table Grid` + `autofit=True`；未固定总宽/列宽；无单元格边距；表头只灰底不加粗；Tips 内表格字体 9.5pt，普通表 10pt；长文本一律居中。 | 脚本约 140-159、167-186 行；python-docx 检查显示所有表 `autofit=True`。 | A4 打印可读性不足，列宽随内容漂移；长中文居中会降低阅读速度；9.5pt 黑白复印后偏小。 |
| 表格跨页 | 表头行未设置重复，行未设置不可拆分。 | XML 未检出 `tblHeader/cantSplit`。 | 长表或页尾表格可能断行，第二页无表头，影响阅读。 |
| 标题/正文跨页 | `add_heading()` 只设置字号、加粗、间距，不设置 `keep_with_next`；正文第一段也无 `keep_together`。 | 脚本约 65-80 行；选中的标题段落 keep flags 均为空。 | 二级/三级标题可能留在页底，正文开到下一页。 |
| 黑白布局 | 使用浅灰填充是正确方向，但没有建立统一灰度层级；Tips 边框较粗、表头灰底偏重，且页面不是 A4。 | `F2F2F2`、`D9D9D9`、黑色 12 边框混用；无渲染校验。 | 黑白打印下 Tips、表格、正文的视觉优先级可能不稳定。 |

## 返工检查清单

| 优先级 | 项目 | 具体动作 | 验收标准 |
| --- | --- | --- | --- |
| P0 | A4 页面 | 在 `build_docx()` 初始化 section 时显式设置 `section.page_width = Cm(21.0)`、`section.page_height = Cm(29.7)`，再设置页边距。 | 生成 DOCX 的 `sectPr/w:pgSz` 接近 A4；python-docx 读数为 21.0cm x 29.7cm。 |
| P0 | 统一字体 | 保留正文宋体小四；Tips 正文不低于 10.5pt；表格正文建议 10.5pt，只有超密表格才降到 10pt，避免 9.5pt。标签可用黑体/微软雅黑或样张字体，正文仍用宋体。 | 黑白打印后表格和 Tips 正文字号不明显小于正文；所有中文 run 设置 `w:eastAsia`。 |
| P0 | Tips 标签 | 重写 `add_tip()` 为 `add_tips_block()`：独立 `铁头tips` 标签区 + 内容区，标签与标题分离；标签建议小块深灰/白字或样张同款；标题行居中加粗。 | 每个 Tips 顶部都有稳定、醒目的 `铁头tips` 标签；标题不再混在同一行普通文本里。 |
| P0 | Tips 边框/底色 | 使用统一灰度：标签深灰，内容浅灰或白底，边框 0.75-1pt；避免整块过重黑框。补充内容若出现，按规则用双线框。 | 黑白预览下 Tips 与正文有清晰边界，但不会像重表格一样抢正文层级。 |
| P0 | Tips 保持同页 | 对 Tips 标签、标题、首段设置 `keep_with_next`；对 Tips 外层表格的行设置 `cantSplit`；短 Tips 整块尽量同页，页底剩余不足时整块移到下页。 | XML 有 `keepNext`/`cantSplit`；抽查 Tips 不出现标签和内容跨页。 |
| P0 | 表格宽度 | 所有表格设置 `table.autofit = False` 和 fixed layout；按 A4 正文宽度分配列宽。四列以上表格优先压缩列名、换行或拆表。 | 表格不会因长词撑宽；A4 版心内完整显示。 |
| P0 | 表头与正文 | 表头加粗、居中、浅/中灰底；正文长中文左对齐，短词居中；单元格加内边距。 | 长句不再整列居中；表头在黑白下清楚可辨。 |
| P0 | 表格跨页 | 表头行设置 `tblHeader`，所有行设置 `cantSplit`；短表应整体不拆，长表允许分页但第二页重复表头。 | XML 检出 `tblHeader/cantSplit`；长表分页仍可读。 |
| P0 | 标题防孤行 | `add_heading()` 对一级、二级、三级标题设置 `keep_with_next=True` 和 `keep_together=True`；正文首段设置 `keep_together=True`。 | 标题不会单独落在页底。 |
| P1 | 表格归属 | 比较表、易混表、总结表原则上放入 Tips 风格块。当前“四种量表”独立表如继续保留，需要管理端确认其作为正文表而非 Tips 表。 | 表格位置符合“总结表/视觉比较放 Tips 内”的规则。 |
| P1 | 空行间距 | Tips 前后按规则保留空行；表格与 Tips 相邻时留两空行。不要用大量空段落硬挤版面，应优先使用段前/段后。 | XML 中空段落数量可控，Word 中间距稳定。 |
| P1 | 黑白校验 | 生成后用 Word/WPS/LibreOffice 导出 PDF 或打印预览，重点看 Tips、表格、标题页尾。当前环境未发现 `libreoffice/soffice`，需在有渲染工具的机器上做最终视觉校验。 | 人工抽查无重叠、无孤立标题、无难读小字。 |

## python-docx 实现建议

### 1. 页面与段落 keep helper

```python
def configure_a4_section(section):
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.4)
    section.right_margin = Cm(2.2)


def keep_paragraph(p, with_next=False, together=True):
    fmt = p.paragraph_format
    fmt.keep_with_next = with_next
    fmt.keep_together = together
    fmt.widow_control = True
```

- `add_heading()` 中调用 `keep_paragraph(p, with_next=True, together=True)`。
- 每个标题后的第一段正文调用 `keep_paragraph(first_body_p, together=True)`。
- 章标题建议继续使用显式分页，但应使用 `paragraph_format.page_break_before=True` 或统一 `add_chapter_heading()`，减少空段落堆版。

### 2. 表格 fixed layout 与行控制

```python
def set_table_fixed(table, widths_cm):
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tbl_pr.append(layout)
    for row in table.rows:
        for idx, cell in enumerate(row.cells):
            cell.width = Cm(widths_cm[idx])
            set_cell_width(cell, widths_cm[idx])
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            set_row_cant_split(row)


def set_row_cant_split(row):
    tr_pr = row._tr.get_or_add_trPr()
    if tr_pr.find(qn("w:cantSplit")) is None:
        tr_pr.append(OxmlElement("w:cantSplit"))


def set_repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    if tr_pr.find(qn("w:tblHeader")) is None:
        tr_pr.append(OxmlElement("w:tblHeader"))


def set_cell_width(cell, width_cm):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.find(qn("w:tcW"))
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:w"), str(int(width_cm * 567)))
    tc_w.set(qn("w:type"), "dxa")


def set_cell_margins(cell, top=80, bottom=80, left=100, right=100):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.find(qn("w:tcMar"))
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for edge, value in {"top": top, "bottom": bottom, "left": left, "right": right}.items():
        node = tc_mar.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")
```

- `add_simple_table()` 和 Tips 内部表都应使用同一套表格 helper。
- 表头 run 设置 bold=True；正文 run 设 10.5pt，长文本 `WD_ALIGN_PARAGRAPH.LEFT`。
- 四种量表表格可按 A4 版心约 16.4cm 分配为 `3.0 / 4.4 / 5.2 / 3.8`，再根据实际文字压缩。

### 3. Tips block 建议结构

建议不要继续把 `铁头Tips：标题` 放在普通首段里。可用两行外层表格模拟样张标签：第一行只放标签，第二行放标题、正文、内嵌表格和来源。

```python
def add_tips_block(doc, title=None, paragraphs=None, table_data=None, source=None):
    add_spacing(doc, before=True)
    outer = doc.add_table(rows=2, cols=1)
    outer.autofit = False
    set_table_fixed(outer, [16.4])
    set_row_cant_split(outer.rows[0])
    set_row_cant_split(outer.rows[1])

    label_cell = outer.cell(0, 0)
    shade_cell(label_cell, "404040")
    set_cell_border(label_cell, bottom={"val": "single", "sz": "8", "color": "000000", "space": "0"})
    label_p = label_cell.paragraphs[0]
    keep_paragraph(label_p, with_next=True)
    label_run = label_p.add_run("铁头tips")
    set_run_font(label_run, size=10.5, bold=True, color=(255, 255, 255))

    body_cell = outer.cell(1, 0)
    shade_cell(body_cell, "F7F7F7")
    if title:
        title_p = body_cell.paragraphs[0]
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        keep_paragraph(title_p, with_next=True)
        set_run_font(title_p.add_run(title), size=11, bold=True)
```

落地时再补齐正文段落、内嵌表格、右下角来源。若管理端提供深大样张，应把标签填充色、边框粗细、标签位置、字体名替换为样张参数；不得借用样张正文内容。

### 4. 分页近似策略

python-docx 不能直接知道 Word 的最终分页位置，应组合三层处理：

- 结构层：标题 keep-with-next、Tips/短表 row cantSplit、长表 header repeat。
- 估算层：对即将插入的 Tips/表格按段落数和行数估算高度；超过当前页剩余空间时提前 `doc.add_page_break()`。
- 渲染层：在有 Word/WPS/LibreOffice 的环境导出 PDF，抽查所有 Tips、表格、二级/三级标题页尾。

## 建议的返工后验证

1. 运行 `python3 scripts/generate_ecnu_measurement_ch1_2.py` 重新生成 DOCX/XLSX。
2. 用 python-docx 或 XML 检查：页面尺寸为 A4；所有标题段落有 `keepNext`；所有表格行有 `cantSplit`；表头有 `tblHeader`；表格 `autofit=False` 且 fixed layout。
3. 抽查 DOCX 文本：Tips 标签统一为 `铁头tips`，标题居中加粗，来源右下；表格正文不低于 10pt，优先 10.5pt。
4. 在 Word/WPS/LibreOffice 做黑白打印预览或 PDF 导出，重点看页底标题、Tips、四种量表表、三要素表。
5. `git diff --check`，确认无 Markdown/脚本空白错误。

## 风险与待确认

- 精确 Tips logo/标签样式需以 `27深大普心一本通（最新版）(1).docx` 或管理端截图确认；当前仓库未找到该文件，本报告不能给出完全一致的视觉参数。
- 没有本地 LibreOffice/Word 渲染器，当前只能做 XML/metadata 级检查；最终跨页效果必须人工预览。
- 当前 DOCX 封面写有“既有人工一本通样例”作为编制依据，若该样例来自 HF 一本通，建议后续改成“格式参考”或从学生版移除，避免被理解为内容来源。
- 当前正文中仍出现“无华东测量真题支撑”等管理端判断语言，这不是本次格式任务主项，但与分支内一本通规则冲突，后续内容返工时应另行处理。
