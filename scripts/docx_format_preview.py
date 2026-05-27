#!/usr/bin/env python3
"""Render a DOCX through LibreOffice for iterative format repair.

This tool is part of the 一本通 generation loop. It turns the generated DOCX
into PDF/page images so the generator can see real pagination and fix Word
formatting problems before sending the file to the leader.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


def run_command(command: list[str], cwd: Path | None = None, timeout: int = 180) -> CommandResult:
    proc = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    return CommandResult(command=command, returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)


def require_tool(name: str) -> str | None:
    return shutil.which(name)


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(2)


def safe_stem(path: Path) -> str:
    stem = re.sub(r"[^A-Za-z0-9._\-\u4e00-\u9fff]+", "_", path.stem).strip("._")
    return stem or "docx"


def make_file_uri(path: Path) -> str:
    return path.resolve().as_uri()


def parse_pdfinfo(pdfinfo_text: str) -> dict[str, str]:
    info: dict[str, str] = {}
    for line in pdfinfo_text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        info[key.strip()] = value.strip()
    return info


def page_size_status(pdfinfo: dict[str, str]) -> tuple[str, str]:
    raw = pdfinfo.get("Page size", "")
    match = re.search(r"([0-9.]+)\s+x\s+([0-9.]+)\s+pts", raw)
    if not match:
        return "RISK", f"未能解析 PDF 页面尺寸：{raw or 'missing'}"
    width = float(match.group(1))
    height = float(match.group(2))
    portrait_a4 = 590 <= width <= 600 and 835 <= height <= 850
    landscape_a4 = 835 <= width <= 850 and 590 <= height <= 600
    if portrait_a4:
        return "OK", f"A4 纵向：{width:.2f} x {height:.2f} pts"
    if landscape_a4:
        return "RISK", f"A4 横向：{width:.2f} x {height:.2f} pts；一本通通常应为 A4 纵向"
    return "RISK", f"非标准 A4 尺寸或边界异常：{width:.2f} x {height:.2f} pts"


def split_pdf_text_by_page(text: str, pages: int) -> list[str]:
    chunks = text.split("\f")
    cleaned = [chunk.strip() for chunk in chunks]
    if len(cleaned) < pages:
        cleaned.extend([""] * (pages - len(cleaned)))
    return cleaned[:pages]


def visible_len(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def inspect_docx_xml(docx_path: Path) -> dict[str, object]:
    result: dict[str, object] = {
        "heading_counts": {},
        "toc_field_found": False,
        "possible_blue_style_colors": [],
        "manual_catalog_like_lines": 0,
        "image_count": 0,
        "table_count": 0,
        "page_break_count": 0,
    }
    try:
        with zipfile.ZipFile(docx_path) as zf:
            names = set(zf.namelist())
            doc_xml = zf.read("word/document.xml").decode("utf-8", errors="ignore") if "word/document.xml" in names else ""
            styles_xml = zf.read("word/styles.xml").decode("utf-8", errors="ignore") if "word/styles.xml" in names else ""
            result["image_count"] = sum(1 for name in names if name.startswith("word/media/"))
            result["table_count"] = doc_xml.count("<w:tbl")
            result["page_break_count"] = doc_xml.count('w:type="page"') + doc_xml.count("<w:lastRenderedPageBreak")
            result["toc_field_found"] = "TOC" in doc_xml and "\\o" in doc_xml
            heading_counts: dict[str, int] = {}
            for style in ("Heading1", "Heading2", "Heading3", "1", "2", "3"):
                count = len(re.findall(rf'<w:pStyle[^>]+w:val="{re.escape(style)}"', doc_xml))
                if count:
                    heading_counts[style] = count
            result["heading_counts"] = heading_counts

            risky_colors: list[str] = []
            for style_id in ("Heading1", "Heading2", "Heading3", "Heading1Char", "Heading2Char", "Heading3Char", "TOC1", "TOC2", "Hyperlink"):
                pattern = rf'<w:style[^>]+w:styleId="{style_id}"[\s\S]*?</w:style>'
                match = re.search(pattern, styles_xml)
                if not match:
                    continue
                style_xml = match.group(0)
                for color in re.findall(r'<w:color[^>]+(?:w:val="([^"]+)"|w:themeColor="([^"]+)")', style_xml):
                    value = next((part for part in color if part), "")
                    if value and value.lower() not in {"000000", "auto"}:
                        risky_colors.append(f"{style_id}:{value}")
            result["possible_blue_style_colors"] = sorted(set(risky_colors))

            # A weak heuristic for hand-made catalog lines: tab before a page number.
            result["manual_catalog_like_lines"] = len(re.findall(r"<w:tab/>[\s\S]{0,160}<w:t>\d+</w:t>", doc_xml))
    except Exception as exc:  # pragma: no cover - reported to user rather than raised
        result["docx_inspection_error"] = str(exc)
    return result


def create_contact_sheets(previews: list[Path], out_dir: Path, max_width: int = 1800) -> list[Path]:
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return []

    if not previews:
        return []
    sheets: list[Path] = []
    thumb_width = 320
    gutter = 28
    label_h = 28
    cols = max(1, min(4, max_width // (thumb_width + gutter)))
    per_sheet = 12
    for sheet_index, start in enumerate(range(0, len(previews), per_sheet), start=1):
        batch = previews[start : start + per_sheet]
        thumbs = []
        for preview in batch:
            with Image.open(preview) as image:
                image = image.convert("RGB")
                ratio = thumb_width / image.width
                thumb = image.resize((thumb_width, max(1, int(image.height * ratio))))
                thumbs.append((preview, thumb))
        rows = (len(thumbs) + cols - 1) // cols
        cell_h = max(thumb.height for _, thumb in thumbs) + label_h + gutter
        sheet = Image.new("RGB", (cols * (thumb_width + gutter) + gutter, rows * cell_h + gutter), "white")
        draw = ImageDraw.Draw(sheet)
        for idx, (preview, thumb) in enumerate(thumbs):
            row, col = divmod(idx, cols)
            x = gutter + col * (thumb_width + gutter)
            y = gutter + row * cell_h
            draw.text((x, y), preview.stem.replace("page-", "page "), fill="black")
            sheet.paste(thumb, (x, y + label_h))
        sheet_path = out_dir / f"contact-sheet-{sheet_index:02d}.png"
        sheet.save(sheet_path, optimize=True)
        sheets.append(sheet_path)
    return sheets


def analyze_preview_images(previews: list[Path]) -> list[dict[str, object]]:
    try:
        from PIL import Image
    except Exception:
        return []

    metrics: list[dict[str, object]] = []
    for preview in previews:
        with Image.open(preview) as image:
            image = image.convert("RGB")
            width, height = image.size
            pixels = image.load()
            min_x, min_y = width, height
            max_x, max_y = -1, -1
            blue_pixels = 0
            nonwhite_pixels = 0
            sample_step = max(1, min(width, height) // 900)
            for y in range(0, height, sample_step):
                for x in range(0, width, sample_step):
                    r, g, b = pixels[x, y]
                    nonwhite = min(r, g, b) < 245
                    if nonwhite:
                        nonwhite_pixels += 1
                        min_x = min(min_x, x)
                        min_y = min(min_y, y)
                        max_x = max(max_x, x)
                        max_y = max(max_y, y)
                    if b > 120 and b > r + 25 and b > g + 15:
                        blue_pixels += 1
            sampled = max(1, ((height + sample_step - 1) // sample_step) * ((width + sample_step - 1) // sample_step))
            if max_y < 0:
                top_blank = 1.0
                bottom_blank = 1.0
                content_height = 0.0
            else:
                top_blank = min_y / height
                bottom_blank = max(0, height - max_y - 1) / height
                content_height = max(0, max_y - min_y + 1) / height
            metrics.append(
                {
                    "page": int(re.search(r"-(\d+)\.png$", preview.name).group(1)),
                    "width": width,
                    "height": height,
                    "content_height_ratio": round(content_height, 3),
                    "top_blank_ratio": round(top_blank, 3),
                    "bottom_blank_ratio": round(bottom_blank, 3),
                    "nonwhite_ratio": round(nonwhite_pixels / sampled, 4),
                    "blue_ratio": round(blue_pixels / sampled, 5),
                }
            )
    return metrics


def markdown_list(paths: Iterable[Path], root: Path) -> str:
    items = []
    for path in paths:
        try:
            rel = path.relative_to(root)
        except ValueError:
            rel = path
        items.append(f"- `{rel.as_posix()}`")
    return "\n".join(items) if items else "- 无"


def build_report(
    *,
    input_docx: Path,
    out_dir: Path,
    output_docx: Path,
    output_pdf: Path,
    previews: list[Path],
    contact_sheets: list[Path],
    commands: list[CommandResult],
    pdfinfo: dict[str, str],
    text_pages: list[str],
    docx_info: dict[str, object],
    visual_metrics: list[dict[str, object]],
    dpi: int,
) -> str:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    pages = int(pdfinfo.get("Pages", "0") or 0)
    page_status, page_note = page_size_status(pdfinfo)
    blank_pages = [idx + 1 for idx, page in enumerate(text_pages) if visible_len(page) < 5]
    short_pages = [idx + 1 for idx, page in enumerate(text_pages) if 5 <= visible_len(page) < 80]
    style_colors = docx_info.get("possible_blue_style_colors", []) or []
    heading_counts = docx_info.get("heading_counts", {}) or {}
    large_bottom_blank_pages = [m["page"] for m in visual_metrics if float(m["bottom_blank_ratio"]) >= 0.35 and float(m["content_height_ratio"]) <= 0.55]
    blue_pages = [m["page"] for m in visual_metrics if float(m["blue_ratio"]) >= 0.0005]

    findings: list[tuple[str, str]] = []
    findings.append(("OK" if output_pdf.exists() else "ERROR", "LibreOffice 成功导出 PDF" if output_pdf.exists() else "LibreOffice 未生成 PDF"))
    findings.append(("OK" if pages > 0 else "ERROR", f"PDF 页数：{pages}" if pages > 0 else "PDF 页数为 0 或无法读取"))
    findings.append((page_status, page_note))
    findings.append(("OK" if len(previews) == pages and pages > 0 else "RISK", f"页面预览图：{len(previews)}/{pages} 页"))
    findings.append(("OK" if not blank_pages else "RISK", "未发现明显空白页" if not blank_pages else f"疑似空白页：{blank_pages}"))
    findings.append(("OK" if not style_colors else "RISK", "未在标题/目录常见样式中发现非黑色样式色" if not style_colors else f"标题/目录样式疑似非黑色：{', '.join(style_colors)}"))
    findings.append(("OK" if not large_bottom_blank_pages else "RISK", "未通过图像指标发现明显页底大空白" if not large_bottom_blank_pages else f"疑似页底大块空白：{large_bottom_blank_pages}"))
    findings.append(("OK" if not blue_pages else "RISK", "未通过渲染图像发现明显蓝色文字" if not blue_pages else f"渲染图像疑似存在蓝色文字页：{blue_pages}"))
    findings.append(("OK" if heading_counts else "RISK", f"检测到标题样式：{heading_counts}" if heading_counts else "未检测到 Heading 1/2/3 样式；目录可能不是基于标题生成"))
    findings.append(("OK" if docx_info.get("toc_field_found") else "RISK", "检测到 TOC 目录域" if docx_info.get("toc_field_found") else "未检测到 TOC 目录域；目录可能是手写或未生成"))

    command_block = "\n".join(
        [
            f"- `{ ' '.join(result.command) }` -> exit {result.returncode}"
            + (f"\n  - stderr: `{result.stderr.strip()[:500]}`" if result.stderr.strip() else "")
            for result in commands
        ]
    )

    findings_md = "\n".join(f"- `{status}` {message}" for status, message in findings)
    blank_note = "无" if not blank_pages else ", ".join(map(str, blank_pages))
    short_note = "无" if not short_pages else ", ".join(map(str, short_pages))

    contact_sheet_text = ", ".join(f"`{p.relative_to(out_dir).as_posix()}`" for p in contact_sheets) if contact_sheets else "未生成"
    visual_lines = [
        "| 页码 | 内容高度占比 | 页顶空白 | 页底空白 | 非白像素占比 | 蓝色像素占比 |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for metric in visual_metrics:
        visual_lines.append(
            f"| {metric['page']} | {metric['content_height_ratio']} | {metric['top_blank_ratio']} | {metric['bottom_blank_ratio']} | {metric['nonwhite_ratio']} | {metric['blue_ratio']} |"
        )
    visual_table = "\n".join(visual_lines) if visual_metrics else "未生成，缺少 Pillow 或页面预览图。"
    return "\n".join(
        [
            "# DOCX 格式渲染报告",
            "",
            f"- 生成时间：{now}",
            f"- 输入文件：`{input_docx}`",
            f"- 输出目录：`{out_dir}`",
            f"- 预览分辨率：{dpi} DPI",
            "",
            "## 渲染产物",
            "",
            f"- DOCX：`{output_docx.relative_to(out_dir).as_posix()}`",
            f"- PDF：`{output_pdf.relative_to(out_dir).as_posix()}`",
            "- 页面预览图：`previews/page-*.png`",
            f"- 联系表：{contact_sheet_text}",
            "",
            "## 格式风险提示",
            "",
            findings_md,
            "",
            "## PDF 基本信息",
            "",
            f"- 页数：{pages}",
            f"- 页面尺寸：{pdfinfo.get('Page size', '未读取')}",
            f"- 疑似空白页：{blank_note}",
            f"- 文字很少、需人工看图确认的页面：{short_note}",
            "",
            "## DOCX 结构检查",
            "",
            f"- 标题样式计数：`{heading_counts}`",
            f"- 目录域 TOC：`{bool(docx_info.get('toc_field_found'))}`",
            f"- 表格数量：`{docx_info.get('table_count')}`",
            f"- 图片数量：`{docx_info.get('image_count')}`",
            f"- 分页符/渲染分页标记数量：`{docx_info.get('page_break_count')}`",
            f"- 标题/目录/超链接样式疑似非黑色：`{style_colors}`",
            f"- 疑似页底大块空白页：`{large_bottom_blank_pages or []}`",
            f"- 渲染图像疑似蓝色文字页：`{blue_pages or []}`",
            "",
            "## 页面视觉指标",
            "",
            visual_table,
            "",
            "## 生成器修复重点",
            "",
            "生成 DOCX 后，先打开 PDF 或联系表，根据这些信号回改 DOCX 生成逻辑：",
            "",
            "- 目录是否像 Word/WPS 自动生成目录，是否存在蓝色标题或蓝色目录文字。",
            "- 章节标题、二级标题、三级标题是否使用正确层级，标题是否孤立在页尾。",
            "- Tips logo 是否和底框在同一页，Tips、补充内容、表格、图片是否被截断跨页。",
            "- 是否出现大块空白；如果由图片比例导致，需重画或调整图片比例，而不是硬分页。",
            "- A4 黑白打印下，图表文字是否足够清晰，不能依赖颜色区分信息。",
            "- 页码是否从正文第一页开始，封面和目录是否未计入正文页码。",
            "",
            "## 页面预览图",
            "",
            markdown_list(previews, out_dir),
            "",
            "## 执行命令",
            "",
            command_block,
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a DOCX render preview bundle for iterative format repair.")
    parser.add_argument("docx", type=Path, help="Input DOCX file")
    parser.add_argument("--out-dir", type=Path, help="Output directory. Defaults to format-preview/docx-render/<docx-stem>")
    parser.add_argument("--dpi", type=int, default=160, help="Preview image DPI; default 160")
    parser.add_argument("--no-contact-sheet", action="store_true", help="Skip PNG contact sheets")
    parser.add_argument("--force", action="store_true", help="Replace an existing output directory")
    args = parser.parse_args()

    input_docx = args.docx.resolve()
    if not input_docx.exists():
        fail(f"DOCX not found: {input_docx}")
    if input_docx.suffix.lower() != ".docx":
        fail("input must be a .docx file")

    lo = require_tool("libreoffice") or require_tool("soffice")
    if not lo:
        fail("LibreOffice is required. Install: sudo apt-get install -y libreoffice-writer libreoffice-core fonts-noto-cjk poppler-utils")
    for tool in ("pdfinfo", "pdftoppm", "pdftotext"):
        if not require_tool(tool):
            fail(f"{tool} is required. Install: sudo apt-get install -y poppler-utils")

    out_dir = (args.out_dir or (REPO_ROOT / "format-preview" / "docx-render" / safe_stem(input_docx))).resolve()
    if out_dir.exists():
        if not args.force:
            fail(f"output directory already exists; pass --force to replace: {out_dir}")
        shutil.rmtree(out_dir)
    previews_dir = out_dir / "previews"
    previews_dir.mkdir(parents=True, exist_ok=True)

    output_docx = out_dir / "output.docx"
    output_pdf = out_dir / "output.pdf"
    output_txt = out_dir / "output.txt"
    shutil.copy2(input_docx, output_docx)

    commands: list[CommandResult] = []
    with tempfile.TemporaryDirectory(prefix="lo-profile-", dir=out_dir) as profile_dir:
        convert_cmd = [
            lo,
            f"-env:UserInstallation={make_file_uri(Path(profile_dir))}",
            "--headless",
            "--norestore",
            "--nodefault",
            "--nolockcheck",
            "--convert-to",
            "pdf:writer_pdf_Export",
            "--outdir",
            str(out_dir),
            str(output_docx),
        ]
        result = run_command(convert_cmd, timeout=240)
        commands.append(result)
        if result.returncode != 0:
            fail(f"LibreOffice conversion failed: {result.stderr or result.stdout}")

    generated_pdf = out_dir / f"{output_docx.stem}.pdf"
    if generated_pdf.exists() and generated_pdf != output_pdf:
        generated_pdf.replace(output_pdf)
    if not output_pdf.exists():
        # LibreOffice may use the original copied filename stem, but keep a broad fallback.
        pdfs = sorted(out_dir.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
        if pdfs:
            pdfs[0].replace(output_pdf)
    if not output_pdf.exists():
        fail("LibreOffice completed but no PDF was produced")

    info_result = run_command(["pdfinfo", str(output_pdf)])
    commands.append(info_result)
    if info_result.returncode != 0:
        fail(f"pdfinfo failed: {info_result.stderr or info_result.stdout}")
    pdfinfo = parse_pdfinfo(info_result.stdout)
    pages = int(pdfinfo.get("Pages", "0") or 0)

    preview_prefix = previews_dir / "page"
    render_result = run_command(["pdftoppm", "-png", "-r", str(args.dpi), str(output_pdf), str(preview_prefix)], timeout=300)
    commands.append(render_result)
    if render_result.returncode != 0:
        fail(f"pdftoppm failed: {render_result.stderr or render_result.stdout}")
    previews = sorted(previews_dir.glob("page-*.png"), key=lambda p: int(re.search(r"-(\d+)\.png$", p.name).group(1)))

    text_result = run_command(["pdftotext", "-layout", str(output_pdf), str(output_txt)], timeout=180)
    commands.append(text_result)
    text = output_txt.read_text(encoding="utf-8", errors="ignore") if output_txt.exists() else ""
    text_pages = split_pdf_text_by_page(text, pages)

    docx_info = inspect_docx_xml(output_docx)
    contact_sheets = [] if args.no_contact_sheet else create_contact_sheets(previews, out_dir)
    visual_metrics = analyze_preview_images(previews)

    report = build_report(
        input_docx=input_docx,
        out_dir=out_dir,
        output_docx=output_docx,
        output_pdf=output_pdf,
        previews=previews,
        contact_sheets=contact_sheets,
        commands=commands,
        pdfinfo=pdfinfo,
        text_pages=text_pages,
        docx_info=docx_info,
        visual_metrics=visual_metrics,
        dpi=args.dpi,
    )
    report_path = out_dir / "format_report.md"
    report_path.write_text(report, encoding="utf-8")

    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
