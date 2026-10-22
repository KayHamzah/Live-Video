#!/usr/bin/env python3
"""Generate transparent 1080x1920 PNG overlays (title + captions) for the dendeng video."""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

GOLD = (255, 196, 61)
ORANGE = (255, 122, 26)
WHITE = (255, 255, 255)
CREAM = (255, 240, 214)
DARK = (28, 14, 6)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def emoji(ch, size):
    # Noto Color Emoji only ships a 109px bitmap strike; render there and scale.
    f = ImageFont.truetype(EMOJI_FONT, 109)
    img = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((0, 0), ch, font=f, embedded_color=True)
    img = img.crop(img.getbbox())
    return img.resize((size, int(size * img.height / img.width)), Image.LANCZOS)


def run_size(run):
    kind, content, f, _ = run
    if kind == "e":
        return f + 8, f  # f is the emoji size here
    l, t, r, b = f.getbbox(content)
    return r - l, b - t


def line_size(runs, gap=14):
    ws = [run_size(r)[0] for r in runs]
    hs = [run_size(r)[1] for r in runs]
    return sum(ws) + gap * (len(runs) - 1), max(hs)


def draw_line(img, runs, cx, cy, gap=14, shadow=True):
    """Draw a list of runs centered at (cx, cy). Runs: ("t", text, font, color) or ("e", char, size, None)."""
    total_w, _ = line_size(runs, gap)
    x = cx - total_w // 2
    shadow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow_layer)
    d = ImageDraw.Draw(img)
    for run in runs:
        kind, content, f, color = run
        w, h = run_size(run)
        if kind == "t":
            l, t, _, _ = f.getbbox(content)
            pos = (x - l, cy - h // 2 - t)
            if shadow:
                sd.text((pos[0] + 4, pos[1] + 6), content, font=f, fill=(0, 0, 0, 200))
            d.text(pos, content, font=f, fill=color, stroke_width=0)
        else:
            em = emoji(content, f)
            img.alpha_composite(em, (x + 4, cy - em.height // 2))
        x += w + gap
    if shadow:
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(7))
        base = Image.new("RGBA", img.size, (0, 0, 0, 0))
        base.alpha_composite(shadow_layer)
        base.alpha_composite(img)
        img.paste(base)


def pill(img, box, fill, radius=None, outline=None, width=0, glow=None):
    if glow:
        g = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(g).rounded_rectangle(box, radius or (box[3] - box[1]) // 2, fill=glow)
        img.alpha_composite(g.filter(ImageFilter.GaussianBlur(22)))
    ImageDraw.Draw(img).rounded_rectangle(
        box, radius or (box[3] - box[1]) // 2, fill=fill, outline=outline, width=width
    )


def title():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # "Dendeng" in script, gold with dark outline
    f = font("Pacifico_400Regular.ttf", 190)
    text = "Dendeng"
    l, t, r, b = f.getbbox(text)
    x, y = (W - (r - l)) // 2 - l, 150 - t
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).text((x, y), text, font=f, fill=(255, 140, 0, 170))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(26)))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((x + 6, y + 10), text, font=f, fill=(0, 0, 0, 220))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    ImageDraw.Draw(img).text((x, y), text, font=f, fill=GOLD, stroke_width=6, stroke_fill=DARK)

    # "EFFORTLESS" banner
    fb = font("Montserrat_900Black.ttf", 92)
    word = "EFFORTLESS"
    bl, bt, br, bb = fb.getbbox(word)
    bw, bh = br - bl, bb - bt
    by = 418
    pill(img, ((W - bw) // 2 - 44, by - 26, (W + bw) // 2 + 44, by + bh + 26), ORANGE,
         radius=22, glow=(255, 110, 0, 150))
    ImageDraw.Draw(img).text(((W - bw) // 2 - bl, by - bt), word, font=fb, fill=WHITE)

    # "menggunakan Food Engine Cooven"
    fs = font("Montserrat_700Bold.ttf", 44)
    draw_line(img, [("t", "menggunakan", fs, CREAM)], W // 2, 600)
    fk = font("Montserrat_900Black.ttf", 62)
    draw_line(img, [("t", "FOOD ENGINE COOVEN", fk, GOLD)], W // 2, 672)
    return img


def caption(lines, box_h=None):
    """Bottom caption card. lines: list of run lists."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gap_y = 26
    sizes = [line_size(r) for r in lines]
    content_h = sum(h for _, h in sizes) + gap_y * (len(lines) - 1)
    card_w = max(w for w, _ in sizes) + 110
    card_h = box_h or content_h + 90
    cy = 1390
    box = ((W - card_w) // 2, cy - card_h // 2, (W + card_w) // 2, cy + card_h // 2)
    pill(img, box, (20, 10, 4, 205), radius=40, outline=GOLD + (255,), width=5,
         glow=(0, 0, 0, 160))
    y = cy - content_h // 2
    for runs, (_, h) in zip(lines, sizes):
        draw_line(img, runs, W // 2, y + h // 2)
        y += h + gap_y
    return img


def smart_cook():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fs = font("Montserrat_800ExtraBold.ttf", 52)
    fb = font("Montserrat_900Black.ttf", 84)
    # small dark tag above a big glowing orange pill
    tw, th = line_size([("t", "Guna fungsi", fs, WHITE)])
    pill(img, ((W - tw) // 2 - 40, 1250 - th // 2 - 22, (W + tw) // 2 + 40, 1250 + th // 2 + 22),
         (20, 10, 4, 205))
    draw_line(img, [("t", "Guna fungsi", fs, WHITE)], W // 2, 1250)
    runs = [("e", "✨", 64, None), ("t", "SMART COOK", fb, WHITE), ("e", "✨", 64, None)]
    bw, bh = line_size(runs, 22)
    box = ((W - bw) // 2 - 50, 1320, (W + bw) // 2 + 50, 1320 + bh + 70)
    pill(img, box, ORANGE, outline=GOLD + (255,), width=6, glow=(255, 120, 0, 190))
    draw_line(img, runs, W // 2, (box[1] + box[3]) // 2, gap=22)
    return img


def shade():
    """Dark gradients at the top and bottom so text stays readable."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(820):
        d.line([(0, y), (W, y)], fill=(10, 5, 0, int(185 * (1 - y / 820) ** 1.6)))
    for y in range(H - 900, H):
        d.line([(0, y), (W, y)], fill=(10, 5, 0, int(150 * ((y - (H - 900)) / 900) ** 1.8)))
    return img


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    shade().save(os.path.join(out_dir, "shade.png"))
    big = font("Montserrat_900Black.ttf", 74)
    mid = font("Montserrat_800ExtraBold.ttf", 58)
    title().save(os.path.join(out_dir, "title.png"))
    caption([
        [("e", "⏱️", 64, None), ("t", "Masak", mid, WHITE), ("t", "2 JAM", big, GOLD)],
        [("t", "tanpa kacau", mid, WHITE)],
    ]).save(os.path.join(out_dir, "cap1.png"))
    caption([
        [("t", "pun", mid, WHITE)],
        [("t", "TAK BERKERAK!", big, GOLD), ("e", "✅", 66, None)],
    ]).save(os.path.join(out_dir, "cap2.png"))
    caption([
        [("t", "Hasilnya daging", mid, WHITE)],
        [("t", "LEMBUT & SEDAP!", big, GOLD), ("e", "😋", 74, None)],
    ]).save(os.path.join(out_dir, "cap3.png"))
    smart_cook().save(os.path.join(out_dir, "smartcook.png"))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "build"))
