# News Image — 21 November 2026

[![News Image](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/c/news-image-20261121)
[![Rank](https://make.fun/badge/news-image-20261121/Ocarsx/news-image-20261121/rank.svg)](https://make.fun/c/news-image-20261121)
[![Reward](https://make.fun/badge/news-image-20261121/Ocarsx/news-image-20261121/reward.svg)](https://make.fun/c/news-image-20261121)

A one-day world-news front page for **Saturday 21 November 2026**, drawn
entirely by `main.py` (Python 3.13 standard library only — no network,
no external files, deterministic output).

## The image

`main.py` writes `entry.png` (1024×1024, PNG) — a newspaper front page
with six stories first reported on 21 November 2026:

1. **South Africa** — the ANC loses its grip on the cities after its
   worst local-election result since 1994 (BBC).
2. **Ukraine** — Zelenskyy rebukes Trump over his friendly description
   of Putin after the trilateral summit in China.
3. **Iran** — Tehran keeps its enriched-uranium red line but stays
   open to a deal with Washington.
4. **United States** — a court sentences Nikhil Gupta to 19+ years over
   the alleged plot to kill a Sikh separatist leader (BBC).
5. **France** — police officers sentenced over the 2020 beating of
   music producer Michel Zecler; racism upheld as aggravating (BBC).
6. **Yemen** — life inside Taiz, a city besieged by the Houthis (BBC).

## Run it

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png
```

## Entry

Built for the [make.fun](https://make.fun/c/news-image-20261121)
competition `news-image-20261121`: sum up 21 November's world news in
one image. The program draws the page from scratch with a hand-rolled
5×7 bitmap font and a pure-stdlib PNG encoder (`zlib` + `struct`).

## License

MIT — see [LICENSE](LICENSE).
