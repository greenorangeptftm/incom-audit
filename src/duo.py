#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Силуэты для первого экрана главной: двое специалистов спиной к спине против закатного солнца.

Берет белый силуэт с прозрачным фоном (src/art/duo-silhouette.webp) и запекает в готовую картинку:
темная петрольная заливка, золотистый контровой свет по краю (сильнее у головы, где за ней солнце),
мягкий ореол и растворение книзу. Результат: src/assets-sverka/hero-duo.webp. Нужен Pillow.

    python3 src/duo.py
"""
import math
import sys
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageFilter
except ImportError:
    print("Нужен Pillow: pip3 install pillow")
    sys.exit(1)

SRC = Path(__file__).resolve().parent
IN = SRC / "art" / "duo-silhouette.webp"
OUT = SRC / "assets-sverka" / "hero-duo.webp"

PAD = 48                      # запас под ореол, px исходника
SUN = (0.37, 0.15)            # где за фигурами солнце, доли рамки силуэта (голова мужчины)
FILL_TOP, FILL_BOT = (20, 36, 44), (7, 24, 34)      # заливка: чуть светлее в дымке сверху, к низу — тени фото
RIM = (255, 206, 150)         # контровой свет
HALO = (255, 170, 96)         # ореол
FADE = (0.60, 1.00)           # растворение книзу: от и до (доли высоты силуэта)
OPACITY = 0.97


def lerp(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def main():
    src = Image.open(IN).convert("RGBA")
    a0 = src.getchannel("A").point(lambda v: 0 if v < 16 else v)       # убираем едва заметный мусор по краям
    a0 = a0.crop(a0.getbbox()).point(lambda v: min(255, round(v * 255 / 224)))   # тело силуэта в исходнике ~88 % непрозрачности
    w, h = a0.size
    W, H = w + 2 * PAD, h + 2 * PAD
    A = Image.new("L", (W, H), 0)
    A.paste(a0, (PAD, PAD))

    # сила контрового света: максимум у головы (за ней солнце), к низу почти нет
    sx, sy = PAD + SUN[0] * w, PAD + SUN[1] * h
    sig = 0.40 * h

    def light(x, y):
        sun = 0.30 + 0.70 * math.exp(-((x - sx) ** 2 + (y - sy) ** 2) / (2 * sig * sig))
        t = min(1, max(0, ((y - PAD) / h - 0.22) / 0.45))
        return sun * (1 - 0.88 * t * t * (3 - 2 * t))

    near = Image.new("L", (W, H))
    near.putdata([round(255 * light(x, y)) for y in range(H) for x in range(W)])

    # заливка: вертикальный градиент
    fill = Image.new("RGB", (W, H))
    fill.putdata([lerp(FILL_TOP, FILL_BOT, min(1, max(0, (y - PAD) / h))) for y in range(H) for x in range(W)])

    # контровой свет: тонкая кромка внутри силуэта
    inner = A.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(1.2))
    rim = ImageChops.subtract(A, inner)
    rim = ImageChops.multiply(rim, near)
    rim = rim.point(lambda v: min(255, round(v * 1.9)))
    body = Image.composite(Image.new("RGB", (W, H), RIM), fill, rim)

    # ореол снаружи
    halo_a = A.filter(ImageFilter.GaussianBlur(16))
    halo_a = ImageChops.subtract(halo_a, A)
    halo_a = ImageChops.multiply(halo_a, near).point(lambda v: round(v * 0.55))
    rim_out = ImageChops.subtract(A.filter(ImageFilter.GaussianBlur(1.6)), A).point(lambda v: min(255, v * 2))
    rim_out = ImageChops.multiply(rim_out, near)

    out = Image.new("RGBA", (W, H), HALO + (0,))
    out.putalpha(halo_a)
    edge = Image.new("RGBA", (W, H), RIM + (0,))
    edge.putalpha(rim_out)
    out = Image.alpha_composite(out, edge)
    fig = body.convert("RGBA")
    fig.putalpha(A.point(lambda v: round(v * OPACITY)))
    out = Image.alpha_composite(out, fig)

    # растворение книзу
    f0, f1 = PAD + FADE[0] * h, PAD + FADE[1] * h
    fade = Image.new("L", (W, H))
    col = []
    for y in range(H):
        t = 0 if y <= f0 else 1 if y >= f1 else (y - f0) / (f1 - f0)
        t = t * t * (3 - 2 * t)
        col.append(round(255 * (1 - t)))
    fade.putdata([col[y] for y in range(H) for x in range(W)])
    out.putalpha(ImageChops.multiply(out.getchannel("A"), fade))

    out = out.crop(out.getchannel("A").point(lambda v: 255 if v > 3 else 0).getbbox())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.save(OUT, "WEBP", quality=86, method=6)
    print("%s %dx%d %d KB" % (OUT, out.width, out.height, OUT.stat().st_size // 1024))
    print("рамка силуэта внутри картинки: pad=%d, w=%d, h=%d" % (PAD, w, h))


if __name__ == "__main__":
    main()
