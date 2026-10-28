#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тонировка фотографий под палитру «Сверка»: петрольные тени, бирюзовые полутона, теплые закатные света.

Берет исходные (натуральные) JPG из папки --raw и складывает готовые файлы в src/photos/,
откуда их забирает build.py. Фото из NATURAL копируются без изменений (главный экран —
эталон палитры, остальные под него подгоняются). Нужен Pillow: pip3 install pillow

    python3 src/tone.py                 # ../incom-redesign/site/assets/photos -> src/photos
    python3 src/tone.py --raw /путь --sheet /tmp/sheet.jpg   # плюс контактный лист для проверки
"""
import argparse
import shutil
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps, ImageEnhance, ImageDraw
except ImportError:
    print("Нужен Pillow: pip3 install pillow")
    sys.exit(1)

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
DEFAULT_RAW = ROOT.parent / "incom-redesign" / "site" / "assets" / "photos"
OUT = SRC / "photos"

# Фото, которые остаются в натуральном цвете
NATURAL = {"moscow-city-sunset"}

# Градиентная карта: яркость 0..1 -> цвет. Тени = петроль сайта, света = теплый закат с главной
STOPS = [
    (0.00, "#061B28"),
    (0.30, "#0D3C55"),
    (0.58, "#2A7390"),
    (0.78, "#C4906A"),
    (0.90, "#F0C3A0"),
    (1.00, "#FFF1E4"),
]
CONTRAST = 1.08
QUALITY = 86


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def luts(stops):
    stops = sorted((p, hexrgb(c)) for p, c in stops)
    out = [[0] * 256 for _ in range(3)]
    for i in range(256):
        t = i / 255
        for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
            if p0 <= t <= p1:
                k = 0 if p1 == p0 else (t - p0) / (p1 - p0)
                for ch in range(3):
                    out[ch][i] = round(c0[ch] + (c1[ch] - c0[ch]) * k)
                break
    return out


LUT = luts(STOPS)


def tone(img):
    g = ImageOps.grayscale(img)
    if CONTRAST != 1.0:
        g = ImageEnhance.Contrast(g).enhance(CONTRAST)
    return Image.merge("RGB", (g.point(LUT[0]), g.point(LUT[1]), g.point(LUT[2])))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--raw", default=str(DEFAULT_RAW), help="папка с исходными JPG")
    ap.add_argument("--out", default=str(OUT), help="куда класть результат (по умолчанию src/photos)")
    ap.add_argument("--sheet", help="сохранить контактный лист результата в этот файл")
    a = ap.parse_args()
    raw, out = Path(a.raw), Path(a.out)
    if not raw.is_dir():
        print("Папка с исходниками не найдена: %s" % raw)
        return 1
    out.mkdir(parents=True, exist_ok=True)
    done, kept, sheet = [], [], []
    for p in sorted(raw.glob("*.jpg")):
        key = p.stem[:-4] if p.stem.endswith("-900") else p.stem
        dst = out / p.name
        if key in NATURAL:
            shutil.copy2(p, dst)
            kept.append(p.name)
            continue
        img = Image.open(p).convert("RGB")
        res = tone(img)
        res.save(dst, "JPEG", quality=QUALITY, optimize=True, progressive=True)
        done.append(p.name)
        if a.sheet and not p.stem.endswith("-900"):
            sheet.append((key, ImageOps.fit(res, (260, 195))))
    print("тонировано %d, скопировано без изменений %d -> %s" % (len(done), len(kept), out))
    if a.sheet and sheet:
        cols = 6
        rows = (len(sheet) + cols - 1) // cols
        im = Image.new("RGB", (cols * 268 + 8, rows * 221 + 8), "#F4F2EE")
        d = ImageDraw.Draw(im)
        for i, (k, t) in enumerate(sheet):
            x, y = 8 + (i % cols) * 268, 8 + (i // cols) * 221
            im.paste(t, (x, y + 18))
            d.text((x, y + 3), k, fill="#111")
        im.save(a.sheet, quality=85)
        print("контактный лист:", a.sheet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
