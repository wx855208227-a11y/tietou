from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


BASE = Path(__file__).resolve().parent
OUT = BASE / "assets" / "modern-intelligence-test-path.png"
FONT = BASE / "assets" / "fonts" / "NotoSansSC-Regular.otf"


def font(size):
    return ImageFont.truetype(str(FONT), size)


def text_size(draw, text, fnt):
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def wrap_text(draw, text, fnt, max_width):
    lines = []
    for para in text.split("\n"):
        current = ""
        for char in para:
            candidate = current + char
            if text_size(draw, candidate, fnt)[0] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = char
        if current:
            lines.append(current)
    return lines


def rounded_box(draw, xy, radius, fill, outline, width=3):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def arrow(draw, start, end, color="#2F4A5A", width=8):
    x1, y1 = start
    x2, y2 = end
    draw.line((x1, y1, x2, y2), fill=color, width=width)
    head = 34
    if abs(x2 - x1) >= abs(y2 - y1):
        direction = 1 if x2 >= x1 else -1
        draw.polygon([(x2, y2), (x2 - direction * head, y2 - head // 2), (x2 - direction * head, y2 + head // 2)], fill=color)
    else:
        direction = 1 if y2 >= y1 else -1
        draw.polygon([(x2, y2), (x2 - head // 2, y2 - direction * head), (x2 + head // 2, y2 - direction * head)], fill=color)


def draw_card(draw, xy, fill, outline, tag, title, body, note=None):
    x1, y1, x2, y2 = xy
    rounded_box(draw, xy, 24, fill, outline, 6)

    tag_f = font(38)
    title_f = font(52)
    body_f = font(41)
    small_f = font(34)

    tag_w, tag_h = text_size(draw, tag, tag_f)
    draw.rounded_rectangle((x1 + 32, y1 + 32, x1 + 80 + tag_w, y1 + 88), radius=18, fill="#111111")
    draw.text((x1 + 56, y1 + 29), tag, font=tag_f, fill="white")

    draw.text((x1 + 148, y1 + 30), title, font=title_f, fill="#111111")

    y = y1 + 105
    for line in wrap_text(draw, body, body_f, x2 - x1 - 96):
        draw.text((x1 + 48, y), line, font=body_f, fill="#111111")
        y += 55

    if note:
        note_w, _ = text_size(draw, note, small_f)
        draw.rounded_rectangle((x2 - note_w - 62, y2 - 64, x2 - 28, y2 - 18), radius=14, fill="#111111")
        draw.text((x2 - note_w - 45, y2 - 69), note, font=small_f, fill="white")


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    width, height = 1800, 1600
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    title_f = font(64)
    sub_f = font(38)
    draw.text((80, 54), "现代智力测验形成路径", font=title_f, fill="#111111")
    draw.text((84, 134), "从早期个别差异测量，到1905年比奈—西蒙量表形成", font=sub_f, fill="#222222")
    draw.line((80, 205, 1720, 205), fill="#111111", width=5)

    # Print-friendly black-and-white background.
    draw.rounded_rectangle((70, 235, 1730, 1430), radius=34, fill="#F4F4F4", outline="#111111", width=5)

    cards = [
        ((120, 285, 1680, 495), "#FFFFFF", "#111111", "01", "方法基础", "冯特提供实验控制、标准化思想；高尔顿/卡特尔推动个别差异测量", None),
        ((120, 575, 1680, 785), "#E8E8E8", "#111111", "02", "问题暴露", "简单感觉、反应时测验与学习成绩等外部指标相关较低", None),
        ((120, 865, 1680, 1075), "#FFFFFF", "#111111", "03", "测量转向", "比奈与亨利主张转向记忆、注意、理解、判断等复杂功能", None),
        ((120, 1155, 1680, 1365), "#E8E8E8", "#111111", "04", "现实结果", "1905年比奈—西蒙量表产生，成为世界上第一个真正意义上的智力测验", None),
    ]

    for item in cards:
        draw_card(draw, *item)

    for y1, y2 in ((505, 565), (795, 855), (1085, 1145)):
        arrow(draw, (900, y1), (900, y2), color="#111111", width=12)

    footer_f = font(40)
    draw.rounded_rectangle((120, 1450, 1680, 1522), radius=18, fill="white", outline="#111111", width=4)
    draw.text((150, 1460), "记忆逻辑：方法基础 → 指标不准 → 高级功能 → 1905年量表形成", font=footer_f, fill="#111111")

    img.save(OUT, quality=95)
    print(OUT)


if __name__ == "__main__":
    main()
