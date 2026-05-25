# 一本通整体格式母版标准

This file records the leader-confirmed overall DOCX formatting standard for 铁头一本通. It is a formatting standard only. Do not use the sample's正文内容、层级判断、真题标注、Tips 内容、语言取舍 or knowledge-point selection as content authority.

## Authoritative Format Sample

- Primary whole-document format sample: `references/format-samples/shenda-general-psychology-yibentong-format-sample.docx`.
- Use this sample for cover, catalog, page numbers, title styles, body text, heading hierarchy, Tips logo/block, supplementary content boxes, table style, fonts, spacing, and A4 print layout.
- Secondary generated Tips comparison sample: `references/format-samples/chapter-01-yibentong-v11-selective-tips.docx`. Use it only as an accepted comparison for generated Tips blocks; when it conflicts with the 深大普心 sample, the 深大普心 sample is the higher-priority format reference.

## Extracted Structure Evidence

The 深大普心 sample contains a real Word/WPS structure, not only manual visual formatting:

- A4 page setup: `11906 x 16838` twips.
- Margins: top/bottom `1440` twips, left/right `1800` twips; header `851`, footer `992`.
- Body styles observed: `Normal`, `Heading 1`, `Heading 2`, `Heading 3`, and `Table Grid`.
- Catalog field observed: `TOC \o "1-2" \h \u`, with page-reference fields. The catalog is generated from heading styles.
- Tips implementation uses VML/textbox logo elements plus shaded paragraphs, not plain正文 labels.
- Supplementary content uses double-line paragraph borders.

## Page And Section Setup

- Use A4 portrait.
- Default margins: top/bottom 2.54 cm; left/right 3.18 cm; header about 1.50 cm; footer about 1.75 cm.
- Use one-column layout.
- Start each chapter on a new page when compiling a multi-chapter document.
- Footer uses Word `PAGE` field for page numbers. Cover/catalog should not be counted as正文 page numbers unless the leader asks otherwise.

## Cover Standard

Follow the 深大 sample's centered cover composition and replace only project-specific text:

- Institution brand line: `铁头心理`, 华文楷体/华文新魏, bold, about 26 pt.
- Main title: `重难点一本通`, centered, bold, about 48 pt.
- School/program line: e.g. `（深圳大学347应用心理专用）`, centered, bold, about 26 pt.
- Subject line: e.g. `普通心理学`, centered, bold, about 72 pt.
- Reference label and reference textbook: centered, bold, about 26 pt.
- Copyright line: centered, bold, about 10 pt.

If 华文楷体、华文新魏, 方正舒体, or Kristen ITC are unavailable in the generation environment, keep the same hierarchy and size relationships, then use a visually close Chinese font. Record the font fallback in the review file.

## Catalog Standard

- Catalog must be generated from Word heading styles, not manually typed.
- Apply `Heading 1` to chapter titles, `Heading 2` to `一、...` titles, and `Heading 3` to `（一）...` titles.
- The 深大 sample's default catalog includes levels 1-2 through `TOC \o "1-2" \h \u`. Use this as the default unless the leader asks for a third-level catalog; if third-level catalog is required, use `TOC \o "1-3" \h \u`.
- After generating or editing a DOCX, update fields in Word/WPS before final export whenever possible. If the local toolchain cannot refresh fields, keep correct heading styles and TOC field codes so the leader can refresh the catalog directly.
- The visible catalog must look like a Word/WPS generated catalog from the 深大 sample, not like a hand-typed placeholder list. Avoid visible placeholder text such as `右键更新域生成目录`, and avoid blue hyperlink-style TOC text in delivered files. If field refresh is unavailable, keep a valid TOC field and provide a conservative black visible result that matches the generated-catalog appearance as closely as possible.

## Title And Body Styles

- Normal正文: 宋体, 小四/12 pt, 1.5 line spacing, justified alignment.
- Body prose paragraphs: first-line indent 2 Chinese characters (`480` twips) when they are continuous explanation sentences.
- Numbered answer-outline lines may omit first-line indent for compactness.
- Chapter title / `Heading 1`: centered, bold, about 16 pt, keep with next; chapter should start on a new page.
- Second-level title / `Heading 2`: left aligned, bold, about 14 pt, spacing before/after about 13 pt.
- Third-level title / `Heading 3`: left aligned, bold, usually 12 pt inherited from Normal, spacing before/after about 13 pt.
- Heading 1/2/3 text must be black. Do not leave default Word blue heading color, hyperlink blue, theme accent color, or other decorative colors in titles or generated catalog text.
- When generating DOCX programmatically, black must be applied not only to `Heading 1/2/3`, but also to related character styles such as `Heading1Char`、`Heading2Char`、`Heading3Char`, plus TOC and hyperlink-related styles when present. Remove or override theme accent colors such as `accent1`; otherwise Word/WPS may still render refreshed headings or catalog links in blue.
- Deeper title levels use正文 style with visible numbering: `1.` level is usually bold; `（1）`、`①`、`A.` are used only when the hierarchy needs them and should remain compact.
- Do not manually fake chapter, second-level, or third-level titles with plain正文 formatting; use the proper heading style so the catalog works.

## Bold, Underline, And Highlight

- Keywords use bold.
- Key phrases or answer-bearing sentence fragments use single underline.
- Do not use highlight color in final正文 unless the leader specifically asks for it.
- Punctuation adjacent to a keyword/key phrase should usually remain unmarked.

## Tips Block Format

Tips are visually independent shaded learning blocks placed after the relevant knowledge point.

- Tips logo/label: `铁头tips`, placed at the upper-left of the block; the sample uses duplicated text boxes for the logo effect.
- Logo font evidence from the sample: `铁头` uses 方正舒体; `tips` uses Kristen ITC/华文行楷; about 10 pt; bold.
- Logo text boxes are transparent/no-fill and positioned over the block, not ordinary正文 labels.
- Tips title: centered and bold when the Tips has a title, e.g. experiment name, `易混辨析：...`, or `图示：...`.
- Tips body: light blue paragraph shading, typically `DAE3F3`; title shading may use `DBE3F4`.
- Tips body正文: 宋体 12 pt, 1.5 line spacing, first-line indent 2 characters for explanatory paragraphs.
- Source/page marker: right aligned in the last shaded paragraph, e.g. `【普通心理学第六版P52】`.
- Keep the logo and shaded body together. Do not let the logo sit on one page and the block body start on the next.
- Do not use a plain one-cell table with `铁头tips` text as a substitute when the output is intended as final DOCX.

## Supplementary Content Format

Supplementary content follows the 深大 sample's double-line box style.

- Start with `补充内容：` in bold.
- Use a black double-line border on all sides of the supplement block. In the sample, bordered paragraphs use `double` border, black, size `4`.
- If the supplement has a specific title, center it and bold it inside the box.
-正文 inside the box follows normal 一本通 marking rules: 宋体 12 pt, concise layered content, bold keywords, underlined key phrases.
- Cite traceable source textbook/page when the supplement is based on another published textbook or literature.
- Keep the whole supplement box together on one page when feasible.

## Tables And Visuals

- Use `Table Grid`-style tables unless a project-specific template requires otherwise.
- Table borders are simple black single lines, about 0.5 pt (`w:sz="4"` in the sample).
- Tables are usually centered on the page; cells are vertically readable and most comparison cells are center aligned.
- Use compact 宋体 text, normally 12 pt or smaller only when needed for fit and still readable in A4 black-and-white printing.
- Do not use decorative colors. If shading is used, it must remain clear in black-and-white printing.
- Comparison tables and diagrams should be placed inside Tips-style blocks when they function as learning aids.

## Layout Self-Check

Before delivery, check these visual issues against the 深大 sample:

- Cover hierarchy and subject/school/reference text are updated correctly.
- Catalog is generated from heading styles and page numbers are refreshable.
- Heading 1/2/3 styles are applied to real headings.
-正文 uses 宋体 12 pt and 1.5 line spacing.
- Tips logo, shaded background, title, body, and source marker stay together.
- Supplementary content uses the double-line box style.
- Tables are compact, readable, and not split awkwardly.
- No title is left at the bottom of a page with its正文 starting on the next page.
- Images, Tips, tables, and supplement boxes are not split across pages when avoidable. Tips tables are especially not allowed to split across pages in ordinary chapter output; if the table does not fit, shorten it, reduce nonessential rows, or move the whole Tips block to the next page.
