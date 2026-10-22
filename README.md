# Live-Video

## Dendeng Effortless — Food Engine Cooven

Video siap: `output/dendeng_food_engine_cooven.mp4` (1080x1920, 30fps, ~20s, untuk Reels/TikTok/Shorts).

Render semula:

```bash
scripts/render.sh                       # guna 2 klip dalam input/
scripts/render.sh klip1.mp4 klip2.mp4 out.mp4
```

- `scripts/make_overlays.py` — jana tajuk & kapsyen (PNG lutsinar) dengan fon Montserrat + Pacifico (`fonts/`, lesen OFL).
- `scripts/render.sh` — gabung klip 1 (slow-mo) → klip 2 (senduk, dasar periuk) → klip 1 terbalik, gred warna hangat, zoom perlahan, animasi teks fade/slide.

Video tiada muzik (trek audio senyap) — tambah lagu trending terus dalam aplikasi media sosial.
