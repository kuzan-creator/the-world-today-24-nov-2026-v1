#!/usr/bin/env python3
"""The World in One Day - Tuesday 24 November 2026, version 1.

Built on the proven v21 template (23 Nov, "The World in One Day"):
cream paper, navy masthead, giant centred serif date headline,
red italic subline, numbers strip, region colour bar, 3 hero
cards (full, bright illustrations), 10 illustrated cards in 2
rows of 5, bright blue-sea world map with real lon/lat land
polygons + region-coloured numbered pins, numbered list of the
remaining 22 stories (every item exactly one line), DATE CHECK
box (3 lines, left-aligned), sources footer. Image 1024x1024.

35 stories, all verified for Tuesday 24 November 2026. Heroes:
Hormuz tanker mines (lead), Zaporizhzhia strike, Gaza security
chief killed. Region bar (story beats, as in v21): EUROPE 10 /
MIDDLE EAST 6 / ASIA-PACIFIC 8 / AMERICAS 6 / TECH & BUSINESS 3
/ SCIENCE & CULTURE 2.

Differences from v21, all forced by this day's stories:
- hero titles are 25 pt, not 26 pt: at 26 pt the Zaporizhzhia
  title wrapped to 3 lines ("Zaporizhzhia" alone on line 3);
  at 25 pt all three titles are exactly 2 lines.
- DATE CHECK now lists 9 exclusions (kuzan's idea, as in
  v20->v21): the v1 four (COP31 collapse 23 Nov, ICJ Rohingya
  ruling Thu 19 Nov, 700,000 tally 23 Nov, Hormuz blockade
  13 Apr / 14 Jul) plus five more verified in v21 - Shenzhen
  (19 Nov), Kerch Bridge (16-17 Nov), Poland missiles
  (20 Nov), FBI hack (20 Nov), Alcaraz win (22 Nov). Its
  three lines are 806.0 / 812.1 / 806.2 px (spread 6.1 px),
  so the balance asserts are back to v21's (min >= 750 px,
  spread < 70 px). Five further v21 exclusions (148-drone
  barrage, Kate documentary, Price darts final, Mayon
  eruption, Lagarde quit) do not fit in 3 lines under the
  839 px limit and are left out - no font or box change.
- list sources are abbreviated where the full name would
  overflow the column ("Kyiv Ind." for Kyiv Independent);
  full names are in README.md. List headlines are shortened
  only where the full headline overflowed (see README).

Deterministic: no network, no randomness, no timestamps in the
art. Running this script twice produces a byte-identical PNG.

Usage:  MAKEFUN_OUTPUT_DIR=<dir> python3 draw.py
Writes <dir>/entry.png (default /output, or the script folder).
"""
import hashlib
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
PAPER = (247, 240, 221)      # cream paper, like the 22 Nov winner
NAVY = (18, 38, 74)          # masthead band
INK = (26, 26, 26)           # headline black
INK_SOFT = (90, 88, 80)
RED = (176, 32, 28)          # brick-red accent
CARD = (255, 253, 247)
LINE = (60, 55, 45)
SEA = (127, 179, 213)        # blue sea on the map
SEAGRID = (150, 195, 225)    # graticule lines on the sea
LANDC = (200, 212, 186)      # pale green land on the map

SERIF_DIR = "/usr/share/fonts/truetype/liberation"
SANS_DIR = "/usr/share/fonts/truetype/dejavu"


def serif(size, bold=False, italic=False):
    if bold and italic:
        name = "LiberationSerif-BoldItalic.ttf"
    elif bold:
        name = "LiberationSerif-Bold.ttf"
    elif italic:
        name = "LiberationSerif-Italic.ttf"
    else:
        name = "LiberationSerif-Regular.ttf"
    return ImageFont.truetype(os.path.join(SERIF_DIR, name), size)


def sans(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(os.path.join(SANS_DIR, name), size)


def wrap(d, text, fnt, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w."""
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if d.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_lines(d, text, fnt, max_w, max_lines):
    """Wrap text, trimming the last line with ' ...' on overflow.

    Returns (lines, trimmed) so the caller can report clipping.
    """
    lines = wrap(d, text, fnt, max_w)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        while lines and d.textlength(lines[-1] + " ...", font=fnt) > max_w:
            lines[-1] = lines[-1][:-1]
        lines[-1] = lines[-1].rstrip() + " ..."
        return lines, True
    return lines, False


def num_badge(d, cx, cy, num, r=11, pt=10):
    """Red disc with a white number, for hero / card corners."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=RED,
              outline=(255, 255, 255), width=1)
    d.text((cx, cy), str(num), font=sans(pt, bold=True),
           fill=(255, 255, 255), anchor="mm")


# ---------------------------------------------------------------- paint helpers
def _lerp(a, b, t):
    return int(a + (b - a) * t + 0.5)


def _vg(d, x0, y0, x1, y1, top, bot):
    """Vertical gradient, one 1 px line per row (deterministic)."""
    h = max(1, int(y1 - y0))
    y0i = int(y0)
    for i in range(h):
        t = i / max(1, h - 1)
        col = tuple(_lerp(top[c], bot[c], t) for c in range(3))
        d.line([(x0, y0i + i), (x1, y0i + i)], fill=col)


def _flame(d, cx, base, w, h):
    """Layered flame rising from (cx, base): orange, gold, pale core."""
    for fw, fh, col in ((w, h, (235, 90, 25)),
                        (w * 0.62, h * 0.68, (250, 170, 40)),
                        (w * 0.34, h * 0.42, (255, 225, 120))):
        d.polygon([(cx - fw / 2, base), (cx - fw * 0.18, base - fh * 0.55),
                   (cx, base - fh), (cx + fw * 0.18, base - fh * 0.55),
                   (cx + fw / 2, base)], fill=col)


def _puff(d, cx, cy, r, col):
    """One soft smoke/cloud puff: four overlapping circles."""
    for dx, dy, rr in ((-0.9, 0.2, 0.55), (0.0, -0.3, 0.7),
                       (0.9, 0.1, 0.5), (0.3, 0.5, 0.45)):
        d.ellipse([cx + dx * r - rr * r, cy + dy * r - rr * r,
                   cx + dx * r + rr * r, cy + dy * r + rr * r], fill=col)

# ---------------------------------------------------------------- stories
# 35 distinct stories for Tuesday 24 November 2026.
HEROES = [
    {"num": 1, "kicker": "STRAIT OF HORMUZ \u00b7 IRAN WAR",
     "title": "Three tankers hit mines as Iran rules out talks",
     "deck": "Tehran vows to use all its tools against the US "
             "blockade; three tankers hit mines and caught fire. "
             "(Reuters)",
     "caption": "Burning tanker \u00b7 Reuters", "scene": "hormuz"},
    {"num": 2, "kicker": "ZAPORIZHZHIA, UKRAINE \u00b7 WAR",
     "title": "Russian strike kills 2, wounds 40 in Zaporizhzhia",
     "deck": "Overnight hit wrecks an apartment block; four children "
             "among the wounded. (Reuters)",
     "caption": "Rescuers at work \u00b7 Reuters", "scene": "kyiv"},
    {"num": 3, "kicker": "GAZA \u00b7 ISRAEL-HAMAS WAR",
     "title": "Israeli strikes kill Hamas security chief",
     "deck": "Naeem Abu Nahel killed in Gaza City; six others dead, "
             "including two police officers. (Reuters)",
     "caption": "Gaza City street \u00b7 Reuters", "scene": "gaza"},
]

# The ten illustrated cards. "region" is the PLACE's region - it
# decides the colour of the location line at the card's bottom-left
# (see the v17 docstring). It is NOT the story's beat: Turin,
# Liverpool and Britain are EUROPE here even though their stories
# sit in the Sport & Culture / Tech & Business beats.
SMALL = [
    {"num": 4, "label": "SPACE THREAT",
     "cap": "NATO vows to defend space after nuclear satellite reports",
     "loc": "BERLIN", "region": "EUROPE", "scene": "space"},
    {"num": 5, "label": "WAR TOLL",
     "cap": "700,000 Russian soldiers killed, new tally finds",
     "loc": "RUSSIA\u2013UKRAINE WAR", "region": "EUROPE",
     "scene": "memorial"},
    {"num": 6, "label": "WARSHIP HIT",
     "cap": "Ukraine claims sinking of Russian warship off Benghazi",
     "loc": "BENGHAZI, LIBYA", "region": "MIDDLE EAST",
     "scene": "warship"},
    {"num": 7, "label": "GENOCIDE RULING",
     "cap": "UK sanctions Myanmar generals after genocide ruling",
     "loc": "LONDON", "region": "EUROPE", "scene": "justice"},
    {"num": 8, "label": "CEO RETURNS",
     "cap": "Nvidia brings back Huang after Trump steps in",
     "loc": "SANTA CLARA, US", "region": "TECH & BUSINESS",
     "scene": "chip"},
    {"num": 9, "label": "COP31 FAILS",
     "cap": "Climate summit ends with no deal on fossil fuels",
     "loc": "ANTALYA, TURKEY", "region": "EUROPE", "scene": "cop31"},
    {"num": 10, "label": "EBOLA TRAPPED",
     "cap": "Fighting traps Ebola teams in Ituri",
     "loc": "ITURI, DR CONGO", "region": "SCIENCE & CULTURE",
     "scene": "clinic"},
    {"num": 11, "label": "M5.6 QUAKE",
     "cap": "5.6 quake strikes Nepal near China border",
     "loc": "NEPAL", "region": "ASIA-PACIFIC", "scene": "quake"},
    {"num": 12, "label": "GROK SUED",
     "cap": "States sue Musk firms over Grok images",
     "loc": "US STATES", "region": "AMERICAS", "scene": "grok"},
    {"num": 13, "label": "$41BN DEAL",
     "cap": "Sanofi to buy Insmed for $41bn",
     "loc": "PARIS", "region": "EUROPE", "scene": "pharma"},
]

# (number, headline, source) - the remaining 22 stories, two columns
# of 11. Headlines are shortened only where the full headline
# overflowed its column (see README.md); sources are abbreviated
# where the full name overflowed ("Kyiv Ind.").
LIST = [
    (14, "Germany first to get Delta system", "Kyiv Ind."),
    (15, "Seven nations back EU Russian visa curbs", "Kyiv Ind."),
    (16, "Zelensky urges NATO to admit Ukraine", "Kyiv Ind."),
    (17, "Russia warns Estonia moves verge of war", "IQMIA"),
    (18, "Russian drone violates Polish airspace", "Kyiv Ind."),
    (19, "Iraq PM: oil ministry to run Kurdish fields", "Reuters"),
    (20, "Oxfam: Gaza now a 'toxic land'", "Oxfam"),
    (21, "Russian jets enter South Korea air zone", "AP"),
    (22, "Hasina to return 16 Dec; Dhaka: handcuffs", "Reuters"),
    (23, "Japan to pay full ICC contribution early", "Reuters"),
    (24, "S. Korea offers $375,000 to catch AI cheats", "WSJ"),
    (25, "Solomon Islands to end China pact", "10Things"),
    (26, "Malaysia to return 6,500 Rohingya", "Medium"),
    (27, "Australia tech fines up to 5% of revenue", "Principia"),
    (28, "US blacklists Singapore cloud firm", "Politico"),
    (29, "Pentagon: Canada falling short on defence", "AP"),
    (30, "US to train Syrian soldiers in demining", "Reuters"),
    (31, "DOJ admits deporting US citizen", "The Hill"),
    (32, "Rep. Gomez to resign after ethics finding", "NYT"),
    (33, "US loses measles elimination status", "Principia"),
    (34, "Pennsylvania's ninth measles death", "Horizon"),
    (35, "Farthest black hole found, 630m yrs on", "Principia"),
]

# Six numbers for the strip - every one taken from the stories above.
NUMBERS = [
    ("3", "tankers hit mines in Hormuz"),
    ("40", "wounded in Zaporizhzhia"),
    ("700,000", "Russian soldiers killed"),
    ("14", "nations back ICJ ruling"),
    ("$41bn", "Sanofi deal for Insmed"),
    ("6,500", "Rohingya to return"),
]

# Region counts - every one of the 35 stories counted once.
REGIONS = [
    ("EUROPE", 10, (46, 95, 163)),
    ("MIDDLE EAST", 6, (176, 32, 28)),
    ("ASIA-PACIFIC", 8, (14, 124, 123)),
    ("AMERICAS", 6, (46, 125, 50)),
    ("TECH & BUSINESS", 3, (108, 79, 161)),
    ("SCIENCE & CULTURE", 2, (183, 121, 31)),
]
REGION_COLOUR = {name: col for name, _, col in REGIONS}

# List-number colour = the story's region (same palette as the bar).
# The card location lines use the place's region (see SMALL
# above), not this list mapping - except card 10, whose place
# (Ituri, DR Congo) has no geographic region in the palette, so it
# uses its story's region (SCIENCE & CULTURE) for its location,
# and card 8, whose place (Santa Clara) is in the AMERICAS but
# whose story is TECH & BUSINESS, which it uses instead.
LIST_REGION = {}
for _n in (14, 15, 16, 17, 18):
    LIST_REGION[_n] = "EUROPE"
for _n in (19, 20, 30):
    LIST_REGION[_n] = "MIDDLE EAST"
for _n in (21, 22, 23, 24, 25, 26, 27):
    LIST_REGION[_n] = "ASIA-PACIFIC"
for _n in (28, 29, 31, 32, 33, 34):
    LIST_REGION[_n] = "AMERICAS"
for _n in (35,):
    LIST_REGION[_n] = "SCIENCE & CULTURE"
del _n

TOTAL_STORIES = 3 + len(SMALL) + len(LIST)
assert TOTAL_STORIES == 35, TOTAL_STORIES
assert sum(c for _, c, _ in REGIONS) == 35
assert [n for n, _, _ in LIST] == list(range(14, 36))
assert all(s["region"] in REGION_COLOUR for s in SMALL)

# Geometry - as v20, except hero titles are 25 pt (see module
# docstring: at 26 pt the Zaporizhzhia title wrapped to 3 lines).
# leading 29, deck offset 100 from the scene bottom, scene 100 px,
# hero 228 px tall. Cards: 129 tall (pitch 133, start y 430),
# picture 70 px, bottom row flush (centre 8 px above the bottom
# edge, badge r=7, 9 pt). Bottom block (v18, restored in v20):
# headers at y=698; the rule under the right-hand header at
# BOTTOM_HDR_Y+20; the list starts at LIST_Y0=724 and ends at
# 918; the map outline keeps its top at MAP_Y0=724 (the subline
# ink ends at y=722, so its 2 px gap is preserved) and its
# bottom is 927 with MAP_BOX (30, 730, 354, 921) - 191 px tall.
# DATE CHECK (v1): box [24, 930, 1000, 992] - 62 px tall, to fit
# exactly three body lines, compact - with a double red outline;
# a red band 115 px wide fills the whole left side of the box,
# full height, its left edge the box's own left border.
# "DATE CHECK" (11 pt bold, 78 px) sits centred in the band. The
# body is 3 hard-coded lines at 10 pt on a 12 px leading,
# LEFT-ALIGNED: every line starts at DC_BODY_X = 154, so the
# left edges form one straight vertical line and the right edges
# are ragged - the line widths are v1's revised (806.0 / 812.1 /
# 806.2 px, spread 6.1 px, all under the 839 px limit): the
# claim line carries the first exclusion (Shenzhen, 19 Nov) and
# lines 2-3 rebalance the rest, as in v21 (830.5 / 801.6 /
# 787.5 px, spread 43 px).
# The y-positions are the ASCENDER TOPS (PIL draws text from the
# ascender, not the baseline): y=942/954/966, chosen so the real
# ink block (944-978) is centred in the box (centre 961) with
# 14 px padding top and bottom.
HERO_Y = 196
HERO_H = 228
HERO_SCENE_H = 100
HERO_TITLE_PT = 25
HERO_TITLE_LEAD = 29
HERO_DECK_OFF = 100
CARD_Y0 = 430
CARD_H = 129
CARD_PITCH = 133
CARD_PIC_H = 70
CARD_HEAD_PT = 12
CARD_HEAD_LEAD = 12  # v1: 12, not v21's 13 - at 13 the 3-line
# headlines' descenders left only a 2 px gap to the location
# line (assert needs >= 3); at 12 the gap is 4 px.
CARD_HEAD_GAP = 4
CARD_LOC_PT = 9
CARD_BOTTOM_ROW = 8
CARD_BADGE_R = 7
CARD_BADGE_PT = 9
LIST_PT = 11
LIST_NUM_PT = 10
LIST_STEP = 18
LIST_Y0 = 724
MAP_Y0 = 724
MAP_BOX = (30, 730, 354, 921)
MAP_BOTTOM = 927
BOTTOM_HDR_Y = 698
DC_BOX = (24, 930, 1000, 992)
DC_BAND_W = 115
DC_TEXT_X0 = 139
DC_TEXT_W = 861
DC_BODY_PAD = 15
DC_BODY_X = DC_TEXT_X0 + DC_BODY_PAD
DC_BODY_Y0 = 942
DC_BODY_LEAD = 12
DC_BODY = [
    "Wires read on Tuesday 24 November 2026. Every story happened, "
    "or was first reported, on 24 November 2026 \u2014 in any time "
    "zone. Left out: Shenzhen (19 Nov);",
    "COP31 collapse (23 Nov) \u2014 a follow-up; ICJ Rohingya "
    "genocide ruling (Thu 19 Nov); 700,000 tally released (23 Nov); "
    "Kerch Bridge (16\u201317 Nov); FBI hack (20 Nov);",
    "Poland missiles (20 Nov); Alcaraz win (22 Nov); Hormuz blockade "
    "first imposed (13 Apr), reinstated (14 Jul) \u2014 the tanker "
    "attacks are 24 Nov; the blockade is not.",
]

# ---------------------------------------------------------------- hero scenes
def _scene_cop31(d, w, h):
    """Summit hall: big COP31 screen with globe, delegate tables
    with flags, an empty chair and one tipped chair (the collapse)."""
    X = lambda f: int(w * f)
    Y = lambda f: int(h * f)
    _vg(d, 0, 0, w, h, (198, 172, 134), (168, 138, 100))
    d.rectangle([0, 0, w, Y(0.10)], fill=(52, 58, 74))
    d.rectangle([X(0.04), Y(0.13), X(0.55), Y(0.52)], fill=(24, 42, 72))
    d.rectangle([X(0.04), Y(0.13), X(0.55), Y(0.52)],
                outline=(212, 178, 90), width=2)
    gx, gy, gr = X(0.14), Y(0.33), 13
    d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill=(64, 140, 190))
    d.ellipse([gx - 9, gy - 8, gx - 1, gy + 1], fill=(96, 178, 110))
    d.ellipse([gx + 2, gy + 2, gx + 10, gy + 10], fill=(96, 178, 110))
    d.ellipse([gx - 2, gy - 11, gx + 6, gy - 4], fill=(96, 178, 110))
    d.text((X(0.27), Y(0.33)), "COP31", font=sans(17, bold=True),
           fill=(255, 255, 255), anchor="lm")
    d.rectangle([X(0.58), Y(0.30), X(0.97), Y(0.42)], fill=(96, 58, 36))
    for i, col in enumerate([(168, 40, 40), (52, 110, 170), (210, 160, 60),
                             (90, 150, 90), (150, 90, 150)]):
        px = X(0.60 + i * 0.075)
        d.ellipse([px, Y(0.20), px + 9, Y(0.30)], fill=(238, 205, 170))
        d.rectangle([px - 2, Y(0.30), px + 11, Y(0.42)], fill=col)
    d.rectangle([X(0.03), Y(0.58), X(0.97), Y(0.72)], fill=(122, 78, 46))
    d.rectangle([X(0.03), Y(0.58), X(0.97), Y(0.62)], fill=(150, 100, 60))
    for i, col in enumerate([(40, 90, 160), (200, 60, 50), (60, 140, 80),
                             (120, 80, 160)]):
        px = X(0.08 + i * 0.14)
        d.ellipse([px, Y(0.46), px + 10, Y(0.58)], fill=(238, 205, 170))
        d.rectangle([px - 2, Y(0.58), px + 12, Y(0.72)], fill=col)
    d.rectangle([X(0.63), Y(0.50), X(0.70), Y(0.72)], fill=(90, 58, 36))
    for fx0, col in ((0.15, (200, 40, 40)), (0.30, (40, 90, 170)),
                     (0.58, (220, 180, 60))):
        d.line([(X(fx0), Y(0.50)), (X(fx0), Y(0.58))], fill=(60, 50, 40),
               width=1)
        d.polygon([(X(fx0), Y(0.50)), (X(fx0) + 9, Y(0.525)),
                   (X(fx0), Y(0.55))], fill=col)
    d.rectangle([0, Y(0.72), w, h], fill=(150, 52, 48))
    d.rectangle([0, Y(0.72), w, Y(0.75)], fill=(120, 38, 36))
    d.polygon([(X(0.82), Y(0.97)), (X(0.90), Y(0.78)),
               (X(0.94), Y(0.83)), (X(0.87), Y(0.99))], fill=(96, 58, 36))
    d.polygon([(X(0.86), Y(0.86)), (X(0.95), Y(0.80)),
               (X(0.97), Y(0.86)), (X(0.89), Y(0.92))], fill=(122, 78, 46))


def _scene_kyiv(d, w, h):
    """Night in Kyiv: a damaged residential tower block with a blast
    hole, a crane overhead, rubble, a small fire and two rescuers
    in orange working the heap."""
    X = lambda f: int(w * f)
    Y = lambda f: int(h * f)
    _vg(d, 0, 0, w, h, (16, 22, 46), (64, 56, 92))
    for sx, sy in ((0.05, 0.08), (0.15, 0.16), (0.30, 0.06), (0.48, 0.12),
                   (0.62, 0.07), (0.95, 0.05)):
        d.ellipse([X(sx) - 1, Y(sy) - 1, X(sx) + 1, Y(sy) + 1],
                  fill=(255, 255, 220))
    d.ellipse([X(0.80) - 8, Y(0.10), X(0.80) + 8, Y(0.10) + 16],
              fill=(235, 225, 190))
    d.rectangle([X(0.46), Y(0.42), X(0.60), h], fill=(28, 32, 52))
    for r in range(3):
        for c in range(2):
            wx, wy = X(0.48) + c * 14, Y(0.48) + r * 12
            d.rectangle([wx, wy, wx + 7, wy + 6],
                        fill=(240, 200, 90) if (r + c) % 2 else (20, 24, 40))
    bx0, bx1 = X(0.06), X(0.42)
    d.polygon([(bx0, h), (bx0, Y(0.22)), (bx0 + 22, Y(0.16)),
               (bx0 + 40, Y(0.26)), (bx0 + 58, Y(0.14)),
               (bx0 + 80, Y(0.24)), (bx1, Y(0.18)), (bx1, h)],
              fill=(36, 42, 60))
    for r in range(4):
        for c in range(4):
            wx, wy = bx0 + 8 + c * 26, Y(0.32) + r * 13
            lit = (r * 4 + c) % 3 != 0
            d.rectangle([wx, wy, wx + 13, wy + 8],
                        fill=(242, 198, 92) if lit else (18, 22, 38))
    hx, hy = bx0 + 52, Y(0.55)
    d.polygon([(hx - 16, hy - 6), (hx - 6, hy - 12), (hx + 8, hy - 8),
               (hx + 14, hy + 2), (hx + 4, hy + 12), (hx - 10, hy + 10)],
              fill=(14, 14, 18))
    d.polygon([(hx - 16, hy - 6), (hx - 6, hy - 12), (hx + 8, hy - 8),
               (hx + 14, hy + 2), (hx + 4, hy + 12), (hx - 10, hy + 10)],
              outline=(250, 140, 50), width=2)
    _puff(d, hx + 6, Y(0.30), 10, (110, 108, 118))
    d.line([(X(0.98), Y(0.02)), (X(0.66), Y(0.52))], fill=(30, 30, 36),
           width=4)
    d.line([(X(0.66), Y(0.52)), (X(0.66), Y(0.66))], fill=(30, 30, 36),
           width=2)
    d.rectangle([X(0.66) - 4, Y(0.66), X(0.66) + 4, Y(0.72)],
                fill=(250, 180, 60))
    d.polygon([(X(0.44), h), (X(0.52), Y(0.72)), (X(0.62), Y(0.80)),
               (X(0.72), Y(0.74)), (X(0.84), Y(0.88)), (X(0.92), h)],
              fill=(96, 98, 110))
    d.polygon([(X(0.55), Y(0.78)), (X(0.63), Y(0.74)),
               (X(0.66), Y(0.80)), (X(0.58), Y(0.84))],
              fill=(150, 152, 164))
    d.polygon([(X(0.70), Y(0.82)), (X(0.78), Y(0.78)),
               (X(0.80), Y(0.85)), (X(0.72), Y(0.88))],
              fill=(140, 142, 154))
    d.ellipse([X(0.60) - 12, Y(0.86), X(0.60) + 12, Y(0.97)],
              fill=(250, 120, 30))
    d.ellipse([X(0.60) - 6, Y(0.90), X(0.60) + 6, Y(0.97)],
              fill=(255, 200, 90))
    rx = X(0.76)
    d.ellipse([rx - 5, Y(0.58), rx + 5, Y(0.66)], fill=(240, 120, 40))
    d.rectangle([rx - 6, Y(0.66), rx + 6, Y(0.78)], fill=(240, 120, 40))
    d.rectangle([rx - 5, Y(0.78), rx - 1, Y(0.86)], fill=(40, 40, 48))
    d.rectangle([rx + 1, Y(0.78), rx + 5, Y(0.86)], fill=(40, 40, 48))
    rx2 = X(0.50)
    d.ellipse([rx2 - 4, Y(0.68), rx2 + 4, Y(0.76)], fill=(240, 120, 40))
    d.rectangle([rx2 - 6, Y(0.76), rx2 + 6, Y(0.86)], fill=(240, 120, 40))


def _scene_hormuz(d, w, h):
    """Burning tanker at dusk: orange sky, low sun, a recognisable
    hull with bridge and funnel, flames mid-deck, smoke drifting
    up and away, waves and a fire reflection on the water."""
    X = lambda f: int(w * f)
    Y = lambda f: int(h * f)
    _vg(d, 0, 0, w, Y(0.52), (238, 132, 58), (252, 196, 118))
    d.ellipse([X(0.80) - 11, Y(0.16), X(0.80) + 11, Y(0.16) + 22],
              fill=(255, 226, 150))
    _vg(d, 0, Y(0.52), w, h, (26, 62, 108), (12, 34, 66))
    d.rectangle([X(0.02), Y(0.47), X(0.16), Y(0.53)], fill=(90, 100, 120))
    d.rectangle([X(0.06), Y(0.42), X(0.10), Y(0.47)], fill=(90, 100, 120))
    d.polygon([(X(0.10), Y(0.60)), (X(0.92), Y(0.60)),
               (X(0.88), Y(0.76)), (X(0.14), Y(0.76))],
              fill=(20, 24, 32))
    d.rectangle([X(0.10), Y(0.60), X(0.92), Y(0.64)], fill=(34, 40, 52))
    d.rectangle([X(0.12), Y(0.72), X(0.90), Y(0.76)], fill=(140, 40, 30))
    d.rectangle([X(0.16), Y(0.56), X(0.60), Y(0.60)], fill=(90, 96, 108))
    d.rectangle([X(0.68), Y(0.40), X(0.84), Y(0.60)], fill=(225, 228, 232))
    d.rectangle([X(0.68), Y(0.40), X(0.84), Y(0.44)], fill=(200, 205, 210))
    for wx in range(4):
        d.rectangle([X(0.70) + wx * 10, Y(0.46),
                     X(0.70) + wx * 10 + 6, Y(0.51)], fill=(40, 70, 110))
    d.rectangle([X(0.60), Y(0.44), X(0.66), Y(0.60)], fill=(120, 40, 30))
    d.rectangle([X(0.60), Y(0.44), X(0.66), Y(0.48)], fill=(240, 200, 90))
    _flame(d, X(0.30), Y(0.57), 24, 22)
    _flame(d, X(0.44), Y(0.57), 28, 28)
    _flame(d, X(0.55), Y(0.57), 18, 18)
    _puff(d, X(0.26), Y(0.18), 12, (58, 56, 62))
    _puff(d, X(0.16), Y(0.13), 10, (70, 68, 74))
    for wy in (0.82, 0.90):
        for k in range(6):
            wx = X(0.02 + k * 0.16)
            d.arc([wx, Y(wy), wx + 22, Y(wy) + 8], 180, 360,
                  fill=(150, 190, 225), width=2)
    for k in range(4):
        d.line([(X(0.30 + k * 0.05), Y(0.80 + k * 0.03)),
                (X(0.42 + k * 0.04), Y(0.80 + k * 0.03))],
               fill=(250, 150, 60), width=2)


def _scene_gaza(d, w, h):
    """Gaza City street in daylight: pale sky, sun, apartment
    blocks (one damaged, smoke rising), a street with rubble, a
    white ambulance with a red cross, and two rescuers in orange
    carrying a stretcher - bright and full, like the other heroes."""
    X = lambda f: int(w * f)
    Y = lambda f: int(h * f)
    _vg(d, 0, 0, w, Y(0.55), (168, 205, 232), (232, 226, 198))
    d.ellipse([X(0.84) - 10, Y(0.10), X(0.84) + 10, Y(0.10) + 20],
              fill=(255, 240, 180))
    # apartment blocks across the back
    for bx0, bx1, top, col in ((0.02, 0.20, 0.30, (196, 178, 150)),
                               (0.22, 0.38, 0.22, (178, 160, 132)),
                               (0.40, 0.58, 0.26, (206, 188, 158)),
                               (0.60, 0.78, 0.20, (186, 168, 140)),
                               (0.80, 0.98, 0.30, (198, 180, 152))):
        d.rectangle([X(bx0), Y(top), X(bx1), Y(0.62)], fill=col)
        d.rectangle([X(bx0), Y(top), X(bx1), Y(0.62)], outline=(120, 105, 85),
                    width=1)
        for r in range(3):
            for c in range(3):
                wx, wy = X(bx0 + 0.02) + c * 14, Y(top + 0.08) + r * 11
                if wx + 8 < X(bx1):
                    d.rectangle([wx, wy, wx + 8, wy + 6],
                                fill=(90, 110, 130))
    # damaged block: blast hole + smoke
    hx, hy = X(0.30), Y(0.42)
    d.polygon([(hx - 14, hy - 4), (hx - 4, hy - 10), (hx + 8, hy - 6),
               (hx + 12, hy + 4), (hx + 2, hy + 10), (hx - 10, hy + 8)],
              fill=(40, 36, 32))
    d.polygon([(hx - 14, hy - 4), (hx - 4, hy - 10), (hx + 8, hy - 6),
               (hx + 12, hy + 4), (hx + 2, hy + 10), (hx - 10, hy + 8)],
              outline=(250, 140, 50), width=2)
    _puff(d, X(0.30), Y(0.16), 11, (96, 94, 100))
    _puff(d, X(0.20), Y(0.11), 8, (110, 108, 112))
    # street
    d.rectangle([0, Y(0.62), w, h], fill=(150, 142, 126))
    d.rectangle([0, Y(0.62), w, Y(0.66)], fill=(120, 112, 98))
    for k in range(5):
        d.rectangle([X(0.04 + k * 0.19), Y(0.80), X(0.12 + k * 0.19),
                     Y(0.83)], fill=(240, 230, 200))
    # rubble heap (low, so the street stays visible)
    d.polygon([(X(0.62), h), (X(0.68), Y(0.80)), (X(0.76), Y(0.84)),
               (X(0.84), Y(0.82)), (X(0.90), h)], fill=(110, 104, 92))
    d.polygon([(X(0.68), Y(0.84)), (X(0.73), Y(0.81)),
               (X(0.76), Y(0.86)), (X(0.70), Y(0.88))],
              fill=(150, 144, 130))
    d.polygon([(X(0.58), Y(0.88)), (X(0.62), Y(0.82)),
               (X(0.65), Y(0.88)), (X(0.60), Y(0.92))],
              fill=(130, 124, 112))
    # ambulance: white van, red cross, blue light
    d.rectangle([X(0.04), Y(0.66), X(0.34), Y(0.88)], fill=(245, 245, 242))
    d.rectangle([X(0.04), Y(0.66), X(0.34), Y(0.88)],
                outline=(160, 160, 160), width=1)
    d.rectangle([X(0.26), Y(0.66), X(0.34), Y(0.76)], fill=(200, 215, 230))
    d.rectangle([X(0.06), Y(0.68), X(0.13), Y(0.76)], fill=(200, 40, 40))
    d.rectangle([X(0.085), Y(0.695), X(0.105), Y(0.745)],
                fill=(245, 245, 242))
    d.rectangle([X(0.065), Y(0.71), X(0.125), Y(0.73)],
                fill=(245, 245, 242))
    d.ellipse([X(0.09), Y(0.88), X(0.13), Y(0.93)], fill=(30, 30, 30))
    d.ellipse([X(0.27), Y(0.88), X(0.31), Y(0.93)], fill=(30, 30, 30))
    d.ellipse([X(0.17), Y(0.63), X(0.21), Y(0.67)], fill=(60, 120, 220))
    # two rescuers in orange carrying a stretcher
    for rx in (0.44, 0.52):
        d.ellipse([X(rx) - 4, Y(0.68), X(rx) + 4, Y(0.75)],
                  fill=(240, 120, 40))
        d.rectangle([X(rx) - 5, Y(0.75), X(rx) + 5, Y(0.86)],
                    fill=(240, 120, 40))
        d.rectangle([X(rx) - 4, Y(0.86), X(rx) - 1, Y(0.93)],
                    fill=(40, 40, 48))
        d.rectangle([X(rx) + 1, Y(0.86), X(rx) + 4, Y(0.93)],
                    fill=(40, 40, 48))
    d.rectangle([X(0.42), Y(0.82), X(0.56), Y(0.86)], fill=(200, 60, 50))


SCENE_HERO = {"cop31": _scene_cop31, "kyiv": _scene_kyiv, "hormuz": _scene_hormuz,
              "gaza": _scene_gaza}

# ---------------------------------------------------------------- small scenes
def _s_capitol(d, w, h):
    """US Capitol: white dome, columns, flag, lawn."""
    _vg(d, 0, 0, w, h, (175, 210, 235), (205, 225, 235))
    d.ellipse([w * 0.8, h * 0.06, w * 0.92, h * 0.2], fill=(255, 245, 200))
    d.rectangle([0, h * 0.78, w, h], fill=(110, 155, 80))
    d.polygon([(w * 0.12, h * 0.78), (w * 0.2, h * 0.68), (w * 0.8, h * 0.68),
               (w * 0.88, h * 0.78)], fill=(235, 235, 230))
    for x in (0.2, 0.28, 0.36, 0.44, 0.52, 0.6, 0.68, 0.76):
        d.rectangle([w * x, h * 0.52, w * (x + 0.03), h * 0.68], fill=(240, 240, 235))
    d.rectangle([w * 0.16, h * 0.5, w * 0.84, h * 0.52], fill=(235, 235, 230))
    d.rectangle([w * 0.3, h * 0.38, w * 0.7, h * 0.5], fill=(245, 245, 240))
    d.polygon([(w * 0.5, h * 0.38), (w * 0.32, h * 0.5), (w * 0.68, h * 0.5)],
              fill=(235, 235, 230))
    d.ellipse([w * 0.56, h * 0.44, w * 0.6, h * 0.48], fill=(180, 180, 170))
    d.pieslice([w * 0.38, h * 0.14, w * 0.62, h * 0.42], 180, 360, fill=(250, 250, 245))
    d.rectangle([w * 0.38, h * 0.36, w * 0.62, h * 0.38], fill=(245, 245, 240))
    d.rectangle([w * 0.48, h * 0.08, w * 0.52, h * 0.16], fill=(250, 250, 245))
    d.line([(w * 0.5, h * 0.08), (w * 0.5, h * 0.02)], fill=(100, 100, 100), width=1)
    d.rectangle([w * 0.5, h * 0.02, w * 0.6, h * 0.06], fill=(200, 40, 40))
    for x in (0.05, 0.14, 0.87, 0.95):
        d.ellipse([w * x, h * 0.62, w * (x + 0.05), h * 0.7], fill=(60, 110, 50))


def _s_oil(d, w, h):
    """Oil market at dusk: pumpjack silhouette, barrels, a green
    rising price arrow - NOT a refinery (the story is the Brent
    price holding above $92, not a strike on a plant)."""
    _vg(d, 0, 0, w, h, (235, 180, 100), (250, 120, 50))
    d.ellipse([w * 0.78, h * 0.12, w * 0.92, h * 0.32],
              fill=(255, 240, 180))
    d.rectangle([0, h * 0.62, w, h], fill=(45, 40, 35))
    # pumpjack silhouette (dark against the dusk sky)
    d.rectangle([w * 0.08, h * 0.60, w * 0.42, h * 0.64], fill=(30, 30, 30))
    d.line([(w * 0.14, h * 0.62), (w * 0.25, h * 0.28)], fill=(30, 30, 30),
           width=3)
    d.line([(w * 0.36, h * 0.62), (w * 0.25, h * 0.28)], fill=(30, 30, 30),
           width=3)
    d.line([(w * 0.10, h * 0.30), (w * 0.44, h * 0.24)], fill=(30, 30, 30),
           width=4)
    d.ellipse([w * 0.42, h * 0.20, w * 0.47, h * 0.28], fill=(30, 30, 30))
    d.rectangle([w * 0.08, h * 0.30, w * 0.13, h * 0.38], fill=(30, 30, 30))
    d.line([(w * 0.44, h * 0.26), (w * 0.44, h * 0.62)], fill=(30, 30, 30),
           width=2)
    d.rectangle([w * 0.41, h * 0.60, w * 0.47, h * 0.64], fill=(20, 20, 20))
    # oil barrels
    for x, y0, col in ((0.55, 0.68, (60, 80, 90)), (0.68, 0.72, (70, 70, 70))):
        d.rectangle([w * x, h * y0, w * (x + 0.11), h * 0.95], fill=col)
        d.ellipse([w * x, h * y0, w * (x + 0.11), h * (y0 + 0.06)],
                  fill=(120, 140, 150))
        d.line([(w * x, h * (y0 + 0.12)), (w * (x + 0.11), h * (y0 + 0.12))],
               fill=(30, 30, 30), width=1)
        d.line([(w * x, h * (y0 + 0.20)), (w * (x + 0.11), h * (y0 + 0.20))],
               fill=(30, 30, 30), width=1)
    # rising price arrow (white halo, then green)
    pts = [(w * 0.52, h * 0.45), (w * 0.62, h * 0.38), (w * 0.70, h * 0.40),
           (w * 0.82, h * 0.22)]
    d.line(pts, fill=(255, 255, 255), width=5, joint="curve")
    d.line(pts, fill=(30, 160, 70), width=3, joint="curve")
    d.polygon([(w * 0.82, h * 0.22), (w * 0.76, h * 0.20), (w * 0.79, h * 0.28)],
              fill=(30, 160, 70))


def _s_warship(d, w, h):
    """Warship at dusk: hull, bridge, mast, waterline."""
    _vg(d, 0, 0, w, h, (240, 200, 130), (220, 120, 60))
    d.ellipse([w * 0.12, h * 0.1, w * 0.26, h * 0.28], fill=(255, 240, 180))
    _vg(d, 0, h * 0.62, w, h, (60, 95, 135), (30, 60, 95))
    for y in (0.68, 0.8, 0.9):
        for x in range(0, 11):
            xx = x * w / 10 + (y * 100 % 2) * w / 20
            d.line([(xx, h * y), (xx + w * 0.04, h * y)], fill=(200, 215, 230), width=1)
    d.polygon([(w * 0.04, h * 0.42), (w * 0.1, h * 0.42), (w * 0.96, h * 0.42),
               (w * 0.9, h * 0.62), (w * 0.06, h * 0.62)], fill=(70, 70, 70))
    d.polygon([(w * 0.06, h * 0.62), (w * 0.9, h * 0.62), (w * 0.88, h * 0.66),
               (w * 0.08, h * 0.66)], fill=(200, 50, 40))
    d.rectangle([w * 0.14, h * 0.3, w * 0.34, h * 0.42], fill=(120, 120, 120))
    d.rectangle([w * 0.18, h * 0.24, w * 0.28, h * 0.3], fill=(100, 100, 100))
    d.rectangle([w * 0.5, h * 0.34, w * 0.56, h * 0.42], fill=(100, 100, 100))
    d.line([(w * 0.3, h * 0.24), (w * 0.3, h * 0.1)], fill=(80, 80, 80), width=2)
    d.ellipse([w * 0.28, h * 0.06, w * 0.32, h * 0.12], fill=(200, 50, 40))
    d.rectangle([w * 0.32, h * 0.1, w * 0.38, h * 0.13], fill=(200, 50, 40))
    d.polygon([(w * 0.4, h * 0.38), (w * 0.44, h * 0.38), (w * 0.42, h * 0.42)],
              fill=(255, 255, 255))
    d.ellipse([w * 0.66, h * 0.42, w * 0.74, h * 0.56], fill=(250, 170, 40))
    d.polygon([(w * 0.62, h * 0.56), (w * 0.78, h * 0.56), (w * 0.7, h * 0.42)],
              fill=(235, 90, 25))
    _flame(d, w * 0.7, h * 0.56, w * 0.08, h * 0.14)
    _puff(d, w * 0.7, h * 0.34, w * 0.05, (60, 60, 60))
    d.polygon([(w * 0.82, h * 0.72), (w * 0.9, h * 0.72), (w * 0.94, h * 0.78),
               (w * 0.78, h * 0.78)], fill=(240, 240, 240))
    d.line([(w * 0.83, h * 0.72), (w * 0.83, h * 0.68)], fill=(80, 80, 80), width=2)
    d.line([(w * 0.83, h * 0.68), (w * 0.88, h * 0.7)], fill=(200, 60, 40), width=1)


def _s_desert(d, w, h):
    """Sinaloa desert: sun, dunes, cactus, road, helicopter."""
    _vg(d, 0, 0, w, h, (250, 210, 120), (250, 160, 70))
    d.ellipse([w * 0.7, h * 0.08, w * 0.9, h * 0.36], fill=(255, 240, 180))
    d.ellipse([w * 0.74, h * 0.12, w * 0.86, h * 0.32], fill=(255, 250, 210))
    d.polygon([(0, h * 0.6), (w * 0.3, h * 0.45), (w * 0.6, h * 0.6),
               (w, h * 0.48), (w, h), (0, h)], fill=(200, 140, 60))
    d.polygon([(0, h * 0.75), (w * 0.4, h * 0.62), (w * 0.7, h * 0.78),
               (w, h * 0.66), (w, h), (0, h)], fill=(180, 120, 50))
    d.rectangle([w * 0.42, h * 0.66, w, h], fill=(50, 50, 50))
    d.line([(w * 0.42, h * 0.66), (w, h)], fill=(255, 220, 120), width=1)
    for x in (0.08, 0.3):
        d.rectangle([w * x, h * 0.5, w * (x + 0.03), h * 0.72], fill=(50, 110, 50))
        d.rectangle([w * (x - 0.03), h * 0.56, w * x, h * 0.6], fill=(50, 110, 50))
        d.rectangle([w * (x + 0.03), h * 0.58, w * (x + 0.06), h * 0.62],
                    fill=(50, 110, 50))
    d.rectangle([w * 0.12, h * 0.3, w * 0.3, h * 0.38], fill=(70, 70, 70))
    d.rectangle([w * 0.32, h * 0.32, w * 0.38, h * 0.38], fill=(70, 70, 70))
    d.line([(w * 0.18, h * 0.3), (w * 0.18, h * 0.24)], fill=(70, 70, 70), width=2)
    d.line([(w * 0.05, h * 0.26), (w * 0.31, h * 0.26)], fill=(70, 70, 70), width=2)
    d.line([(w * 0.18, h * 0.38), (w * 0.18, h * 0.44)], fill=(70, 70, 70), width=2)
    d.line([(w * 0.05, h * 0.42), (w * 0.12, h * 0.44)], fill=(70, 70, 70), width=2)
    d.line([(w * 0.24, h * 0.42), (w * 0.31, h * 0.44)], fill=(70, 70, 70), width=2)
    d.polygon([(w * 0.55, h * 0.72), (w * 0.6, h * 0.72), (w * 0.62, h * 0.78),
               (w * 0.53, h * 0.78)], fill=(255, 255, 255))


def _s_talks(d, w, h):
    """Himalayas: snow peaks, flags, table, treaty."""
    _vg(d, 0, 0, w, h, (200, 220, 240), (240, 240, 240))
    d.polygon([(0, h * 0.75), (w * 0.2, h * 0.3), (w * 0.45, h * 0.75)],
              fill=(120, 140, 160))
    d.polygon([(w * 0.3, h * 0.75), (w * 0.55, h * 0.15), (w * 0.8, h * 0.75)],
              fill=(100, 125, 150))
    d.polygon([(w * 0.6, h * 0.75), (w * 0.82, h * 0.35), (w, h * 0.75)],
              fill=(130, 150, 170))
    d.polygon([(w * 0.16, h * 0.38), (w * 0.2, h * 0.3), (w * 0.24, h * 0.38),
               (w * 0.22, h * 0.42), (w * 0.18, h * 0.42)], fill=(255, 255, 255))
    d.polygon([(w * 0.51, h * 0.23), (w * 0.55, h * 0.15), (w * 0.59, h * 0.23),
               (w * 0.57, h * 0.28), (w * 0.53, h * 0.28)], fill=(255, 255, 255))
    d.polygon([(w * 0.78, h * 0.42), (w * 0.82, h * 0.35), (w * 0.86, h * 0.42),
               (w * 0.84, h * 0.46), (w * 0.8, h * 0.46)], fill=(255, 255, 255))
    for x in (0.06, 0.86):
        d.polygon([(w * x, h * 0.6), (w * (x + 0.06), h * 0.7), (w * (x + 0.12), h * 0.6)],
                  fill=(50, 100, 60))
    d.rectangle([w * 0.35, h * 0.8, w * 0.65, h * 0.9], fill=(120, 70, 40))
    d.rectangle([w * 0.36, h * 0.78, w * 0.64, h * 0.8], fill=(200, 170, 120))
    d.rectangle([w * 0.42, h * 0.72, w * 0.58, h * 0.78], fill=(255, 255, 255))
    d.line([(w * 0.45, h * 0.74), (w * 0.55, h * 0.74)], fill=(60, 60, 60), width=1)
    d.line([(w * 0.45, h * 0.76), (w * 0.53, h * 0.76)], fill=(60, 60, 60), width=1)
    d.line([(w * 0.16, h * 0.62), (w * 0.16, h * 0.3)], fill=(100, 80, 60), width=2)
    d.rectangle([w * 0.16, h * 0.3, w * 0.28, h * 0.44], fill=(255, 140, 50))
    d.ellipse([w * 0.2, h * 0.34, w * 0.24, h * 0.4], fill=(20, 60, 140))
    d.line([(w * 0.84, h * 0.62), (w * 0.84, h * 0.3)], fill=(100, 80, 60), width=2)
    d.rectangle([w * 0.84, h * 0.3, w * 0.96, h * 0.44], fill=(200, 40, 40))
    d.ellipse([w * 0.88, h * 0.34, w * 0.92, h * 0.4], fill=(255, 220, 0))
    d.ellipse([w * 0.42, h * 0.62, w * 0.46, h * 0.68], fill=(240, 210, 120))
    d.ellipse([w * 0.56, h * 0.62, w * 0.6, h * 0.68], fill=(240, 210, 120))

def _s_volcano(d, w, h):
    """Mayon: ash plume, lava flow, village, car, smoke."""
    _vg(d, 0, 0, w, h, (200, 190, 170), (240, 225, 200))
    d.polygon([(w * 0.18, h * 0.9), (w * 0.5, h * 0.35), (w * 0.82, h * 0.9)],
              fill=(80, 70, 60))
    d.polygon([(w * 0.44, h * 0.44), (w * 0.5, h * 0.35), (w * 0.56, h * 0.44),
               (w * 0.54, h * 0.48), (w * 0.46, h * 0.48)], fill=(255, 255, 255))
    _puff(d, w * 0.5, h * 0.26, w * 0.08, (100, 100, 100))
    _puff(d, w * 0.62, h * 0.18, w * 0.06, (120, 120, 120))
    _puff(d, w * 0.38, h * 0.2, w * 0.05, (110, 110, 110))
    d.polygon([(w * 0.47, h * 0.48), (w * 0.53, h * 0.48), (w * 0.6, h * 0.9),
               (w * 0.4, h * 0.9)], fill=(235, 90, 25))
    d.polygon([(w * 0.49, h * 0.48), (w * 0.51, h * 0.48), (w * 0.54, h * 0.9),
               (w * 0.46, h * 0.9)], fill=(255, 200, 60))
    d.rectangle([0, h * 0.9, w, h], fill=(120, 110, 90))
    for x in (0.05, 0.2, 0.75, 0.88):
        d.rectangle([w * x, h * 0.82, w * (x + 0.08), h * 0.9], fill=(60, 60, 60))
        d.polygon([(w * x, h * 0.82), (w * (x + 0.04), h * 0.76),
                   (w * (x + 0.08), h * 0.82)], fill=(120, 60, 50))
    d.rectangle([w * 0.65, h * 0.84, w * 0.72, h * 0.88], fill=(200, 60, 40))
    d.ellipse([w * 0.66, h * 0.88, w * 0.68, h * 0.9], fill=(20, 20, 20))
    d.ellipse([w * 0.7, h * 0.88, w * 0.72, h * 0.9], fill=(20, 20, 20))

def _s_rugby(d, w, h):
    """Rugby in daylight: H-shaped posts, try line, Springboks
    (green/gold) vs France (blue), oval ball - distinct from the
    night football scene (floodlights, rectangular goal, round
    ball)."""
    _vg(d, 0, 0, w, h, (150, 190, 220), (205, 225, 235))
    d.rectangle([0, h * 0.28, w, h * 0.34], fill=(230, 230, 230))
    for x in range(14):
        d.rectangle([w * (0.02 + x * 0.07), h * 0.29,
                     w * (0.045 + x * 0.07), h * 0.33],
                    fill=(180, 180, 180))
    d.rectangle([0, h * 0.34, w, h], fill=(50, 110, 60))
    d.rectangle([w * 0.08, h * 0.42, w * 0.92, h * 0.95], fill=(70, 150, 80))
    d.rectangle([w * 0.08, h * 0.42, w * 0.92, h * 0.95],
                outline=(255, 255, 255), width=2)
    d.line([(w * 0.08, h * 0.68), (w * 0.92, h * 0.68)],
           fill=(255, 255, 255), width=2)
    # H-shaped goalposts (tall, centre-left)
    d.line([(w * 0.30, h * 0.42), (w * 0.30, h * 0.80)],
           fill=(255, 255, 255), width=3)
    d.line([(w * 0.40, h * 0.42), (w * 0.40, h * 0.80)],
           fill=(255, 255, 255), width=3)
    d.line([(w * 0.30, h * 0.58), (w * 0.40, h * 0.58)],
           fill=(255, 255, 255), width=3)
    # Springbok (green) carrying the oval ball
    d.line([(w * 0.55, h * 0.55), (w * 0.55, h * 0.72)], fill=(20, 90, 40),
           width=3)
    d.line([(w * 0.55, h * 0.72), (w * 0.50, h * 0.88)], fill=(20, 90, 40),
           width=3)
    d.line([(w * 0.55, h * 0.72), (w * 0.60, h * 0.88)], fill=(20, 90, 40),
           width=3)
    d.ellipse([w * 0.53, h * 0.50, w * 0.57, h * 0.55], fill=(230, 200, 150))
    d.line([(w * 0.55, h * 0.58), (w * 0.62, h * 0.62)], fill=(20, 90, 40),
           width=3)
    d.ellipse([w * 0.60, h * 0.58, w * 0.68, h * 0.64], fill=(140, 90, 40))
    d.line([(w * 0.63, h * 0.58), (w * 0.65, h * 0.64)],
           fill=(255, 255, 255), width=1)
    # French chaser (blue)
    d.line([(w * 0.72, h * 0.58), (w * 0.72, h * 0.75)],
           fill=(30, 60, 160), width=3)
    d.line([(w * 0.72, h * 0.75), (w * 0.67, h * 0.90)],
           fill=(30, 60, 160), width=3)
    d.line([(w * 0.72, h * 0.75), (w * 0.77, h * 0.90)],
           fill=(30, 60, 160), width=3)
    d.ellipse([w * 0.70, h * 0.53, w * 0.74, h * 0.58], fill=(230, 200, 150))
    d.line([(w * 0.72, h * 0.61), (w * 0.66, h * 0.66)],
           fill=(30, 60, 160), width=3)
    # second Springbok (green), far right
    d.line([(w * 0.85, h * 0.60), (w * 0.85, h * 0.76)], fill=(20, 90, 40),
           width=3)
    d.line([(w * 0.85, h * 0.76), (w * 0.81, h * 0.90)], fill=(20, 90, 40),
           width=3)
    d.line([(w * 0.85, h * 0.76), (w * 0.89, h * 0.90)], fill=(20, 90, 40),
           width=3)
    d.ellipse([w * 0.83, h * 0.55, w * 0.87, h * 0.60], fill=(230, 200, 150))


def _s_football(d, w, h):
    """Football at night: floodlit pitch, goal, players, stands."""
    _vg(d, 0, 0, w, h, (20, 40, 70), (40, 60, 90))
    for x in (0.05, 0.28, 0.7, 0.93):
        d.rectangle([w * x, h * 0.05, w * (x + 0.05), h * 0.1], fill=(200, 200, 200))
        d.rectangle([w * x, h * 0.1, w * (x + 0.02), h * 0.3], fill=(100, 100, 100))
        d.rectangle([w * (x + 0.03), h * 0.1, w * (x + 0.05), h * 0.3],
                    fill=(100, 100, 100))
        d.rectangle([w * x, h * 0.12, w * (x + 0.05), h * 0.16], fill=(220, 220, 220))
    d.rectangle([0, h * 0.35, w, h * 0.42], fill=(60, 60, 60))
    for x in range(16):
        d.rectangle([w * (0.01 + x * 0.06), h * 0.36, w * (0.04 + x * 0.06), h * 0.41],
                    fill=(150, 150, 150))
    d.rectangle([0, h * 0.42, w, h], fill=(40, 100, 50))
    d.rectangle([w * 0.08, h * 0.5, w * 0.92, h * 0.95], fill=(60, 140, 70))
    d.rectangle([w * 0.08, h * 0.5, w * 0.92, h * 0.95], outline=(255, 255, 255), width=2)
    d.ellipse([w * 0.42, h * 0.6, w * 0.58, h * 0.85], outline=(255, 255, 255), width=2)
    d.line([(w * 0.5, h * 0.5), (w * 0.5, h * 0.95)], fill=(255, 255, 255), width=2)
    d.rectangle([w * 0.08, h * 0.62, w * 0.22, h * 0.84], outline=(255, 255, 255), width=2)
    d.rectangle([w * 0.78, h * 0.62, w * 0.92, h * 0.84], outline=(255, 255, 255), width=2)
    d.rectangle([w * 0.08, h * 0.68, w * 0.14, h * 0.78], outline=(255, 255, 255), width=2)
    d.rectangle([w * 0.86, h * 0.68, w * 0.92, h * 0.78], outline=(255, 255, 255), width=2)
    d.line([(w * 0.24, h * 0.6), (w * 0.24, h * 0.48)], fill=(200, 40, 40), width=2)
    d.ellipse([w * 0.22, h * 0.46, w * 0.26, h * 0.5], fill=(200, 40, 40))
    d.line([(w * 0.24, h * 0.6), (w * 0.3, h * 0.66)], fill=(200, 40, 40), width=2)
    d.line([(w * 0.24, h * 0.6), (w * 0.18, h * 0.66)], fill=(200, 40, 40), width=2)
    d.ellipse([w * 0.72, h * 0.68, w * 0.76, h * 0.74], fill=(255, 255, 255))
    d.line([(w * 0.24, h * 0.58), (w * 0.3, h * 0.5)], fill=(200, 40, 40), width=2)
    d.line([(w * 0.3, h * 0.5), (w * 0.36, h * 0.46)], fill=(120, 120, 120), width=2)
    d.ellipse([w * 0.35, h * 0.44, w * 0.37, h * 0.47], fill=(255, 255, 255))
    d.line([(w * 0.66, h * 0.74), (w * 0.66, h * 0.66)], fill=(255, 255, 255), width=2)
    d.ellipse([w * 0.64, h * 0.64, w * 0.68, h * 0.68], fill=(255, 255, 255))
    d.line([(w * 0.66, h * 0.74), (w * 0.7, h * 0.8)], fill=(255, 255, 255), width=2)
    d.line([(w * 0.66, h * 0.74), (w * 0.62, h * 0.8)], fill=(255, 255, 255), width=2)
    d.ellipse([w * 0.44, h * 0.76, w * 0.5, h * 0.84], fill=(255, 255, 255))
    d.polygon([(w * 0.46, h * 0.76), (w * 0.48, h * 0.78), (w * 0.46, h * 0.8)],
              fill=(0, 0, 0))
    d.polygon([(w * 0.48, h * 0.8), (w * 0.5, h * 0.78), (w * 0.48, h * 0.76)],
              fill=(0, 0, 0))


def _s_nhs(d, w, h):
    """NHS scanner: MRI machine, patient, AI bounding box."""
    _vg(d, 0, 0, w, h, (240, 240, 240), (200, 210, 220))
    d.rectangle([0, h * 0.75, w, h], fill=(180, 190, 200))
    d.rounded_rectangle([w * 0.08, h * 0.2, w * 0.92, h * 0.75], radius=8,
                        fill=(200, 210, 220), outline=(150, 160, 170), width=2)
    d.ellipse([w * 0.35, h * 0.32, w * 0.65, h * 0.68], fill=(30, 30, 30))
    d.ellipse([w * 0.38, h * 0.36, w * 0.62, h * 0.64], fill=(240, 240, 240))
    d.rectangle([w * 0.3, h * 0.62, w * 0.7, h * 0.72], fill=(180, 190, 200))
    d.rectangle([w * 0.3, h * 0.62, w * 0.7, h * 0.72], outline=(150, 160, 170), width=1)
    d.ellipse([w * 0.44, h * 0.5, w * 0.56, h * 0.62], fill=(240, 210, 120))
    d.rectangle([w * 0.42, h * 0.6, w * 0.58, h * 0.68], fill=(200, 220, 240))
    d.rectangle([w * 0.14, h * 0.22, w * 0.34, h * 0.42], fill=(20, 80, 160))
    d.text((w * 0.24, h * 0.28), "AI", font=sans(11, bold=True),
           fill=(255, 255, 255), anchor="mm")
    d.text((w * 0.24, h * 0.37), "SCAN", font=sans(6, bold=True),
           fill=(255, 255, 255), anchor="mm")
    d.rectangle([w * 0.62, h * 0.22, w * 0.86, h * 0.42], fill=(255, 255, 255),
                outline=(20, 80, 160), width=2)
    d.line([(w * 0.62, h * 0.22), (w * 0.68, h * 0.22)], fill=(20, 80, 160), width=3)
    d.line([(w * 0.62, h * 0.22), (w * 0.62, h * 0.28)], fill=(20, 80, 160), width=3)
    d.line([(w * 0.86, h * 0.42), (w * 0.8, h * 0.42)], fill=(20, 80, 160), width=3)
    d.line([(w * 0.86, h * 0.42), (w * 0.86, h * 0.36)], fill=(20, 80, 160), width=3)
    d.ellipse([w * 0.7, h * 0.28, w * 0.78, h * 0.36], fill=(200, 40, 40))
    d.text((w * 0.74, h * 0.32), "!", font=sans(8, bold=True),
           fill=(255, 255, 255), anchor="mm")
    for x in (0.05, 0.15, 0.85, 0.95):
        d.ellipse([w * x, h * 0.85, w * (x + 0.03), h * 0.9], fill=(100, 100, 100))


def _s_quake(d, w, h):
    """Quake: seismograph trace, leaning buildings, dust."""
    _vg(d, 0, 0, w, h, (220, 210, 190), (200, 180, 150))
    d.rectangle([0, h * 0.7, w, h], fill=(120, 110, 90))
    d.rectangle([w * 0.1, h * 0.3, w * 0.3, h * 0.7], fill=(80, 80, 80))
    d.rectangle([w * 0.1, h * 0.3, w * 0.3, h * 0.7], outline=(60, 60, 60), width=2)
    for y in (0.38, 0.48, 0.58):
        for x in (0.14, 0.2, 0.26):
            d.rectangle([w * x, h * y, w * (x + 0.02), h * (y + 0.04)],
                        fill=(240, 200, 90))
    d.polygon([(w * 0.45, h * 0.35), (w * 0.65, h * 0.35), (w * 0.6, h * 0.7),
               (w * 0.5, h * 0.7)], fill=(100, 100, 100))
    d.polygon([(w * 0.45, h * 0.35), (w * 0.65, h * 0.35), (w * 0.6, h * 0.7),
               (w * 0.5, h * 0.7)], outline=(70, 70, 70), width=2)
    for y in (0.42, 0.52, 0.62):
        for x in (0.5, 0.56):
            d.rectangle([w * x, h * y, w * (x + 0.02), h * (y + 0.04)],
                        fill=(240, 200, 90))
    d.rectangle([w * 0.75, h * 0.4, w * 0.9, h * 0.7], fill=(90, 90, 90))
    d.rectangle([w * 0.75, h * 0.4, w * 0.9, h * 0.7], outline=(60, 60, 60), width=2)
    d.line([(w * 0.75, h * 0.4), (w * 0.9, h * 0.55)], fill=(60, 60, 60), width=2)
    d.line([(w * 0.75, h * 0.55), (w * 0.9, h * 0.4)], fill=(60, 60, 60), width=2)
    d.rectangle([w * 0.78, h * 0.48, w * 0.82, h * 0.54], fill=(240, 200, 90))
    d.rectangle([w * 0.84, h * 0.58, w * 0.88, h * 0.64], fill=(240, 200, 90))
    d.line([(w * 0.05, h * 0.1), (w * 0.15, h * 0.1), (w * 0.2, h * 0.05),
            (w * 0.25, h * 0.15), (w * 0.3, h * 0.1), (w * 0.35, h * 0.02),
            (w * 0.4, h * 0.18), (w * 0.45, h * 0.1), (w * 0.5, h * 0.05),
            (w * 0.55, h * 0.15), (w * 0.6, h * 0.1), (w * 0.65, h * 0.08),
            (w * 0.7, h * 0.12), (w * 0.75, h * 0.1), (w * 0.8, h * 0.06),
            (w * 0.85, h * 0.14), (w * 0.9, h * 0.1), (w * 0.95, h * 0.08)],
           fill=(200, 40, 40), width=2)
    d.rectangle([w * 0.05, h * 0.05, w * 0.95, h * 0.2], outline=(150, 150, 150), width=1)
    for x in (0.3, 0.45, 0.6, 0.75):
        for y in (0.75, 0.8, 0.85):
            if (x * 100 + y * 100) % 3 < 2:
                d.polygon([(w * x, h * y), (w * (x + 0.03), h * y),
                           (w * (x + 0.015), h * (y - 0.04))], fill=(100, 90, 70))



def _s_space(d, w, h):
    """NATO space defence: deep-blue sky, stars, a satellite with
    gold panels and a dish, Earth curving along the bottom."""
    _vg(d, 0, 0, w, h, (12, 24, 58), (30, 60, 120))
    for sx, sy in ((0.06, 0.10), (0.16, 0.22), (0.30, 0.08), (0.55, 0.14),
                   (0.70, 0.06), (0.88, 0.18), (0.94, 0.32), (0.42, 0.26)):
        d.ellipse([w * sx - 1, h * sy - 1, w * sx + 1, h * sy + 1],
                  fill=(255, 255, 220))
    d.ellipse([0, h * 0.78, w, h * 1.6], fill=(50, 120, 180))
    d.ellipse([0, h * 0.78, w, h * 1.6], outline=(120, 190, 230), width=2)
    d.polygon([(w * 0.05, h * 0.82), (w * 0.3, h * 0.86), (w * 0.6, h * 0.9),
               (w * 0.95, h * 0.86), (w, h), (0, h)], fill=(70, 150, 90))
    # satellite body + gold panels + dish
    d.rectangle([w * 0.38, h * 0.34, w * 0.62, h * 0.52], fill=(220, 225, 230))
    d.rectangle([w * 0.38, h * 0.34, w * 0.62, h * 0.52],
                outline=(150, 155, 165), width=1)
    d.rectangle([w * 0.08, h * 0.38, w * 0.36, h * 0.48], fill=(230, 180, 60))
    d.rectangle([w * 0.08, h * 0.38, w * 0.36, h * 0.48],
                outline=(180, 130, 30), width=1)
    d.rectangle([w * 0.64, h * 0.38, w * 0.92, h * 0.48], fill=(230, 180, 60))
    d.rectangle([w * 0.64, h * 0.38, w * 0.92, h * 0.48],
                outline=(180, 130, 30), width=1)
    for x in (0.16, 0.24, 0.32, 0.72, 0.80, 0.88):
        d.line([(w * x, h * 0.38), (w * x, h * 0.48)], fill=(180, 130, 30),
               width=1)
    d.ellipse([w * 0.44, h * 0.38, w * 0.56, h * 0.48], fill=(60, 120, 200))
    d.line([(w * 0.5, h * 0.34), (w * 0.5, h * 0.26)], fill=(200, 200, 200),
           width=2)
    d.ellipse([w * 0.46, h * 0.22, w * 0.54, h * 0.28], fill=(200, 60, 50))
    # red warning ring around the satellite
    d.ellipse([w * 0.34, h * 0.28, w * 0.66, h * 0.58],
              outline=(255, 80, 60), width=2)


def _s_memorial(d, w, h):
    """War toll memorial at dusk: orange sky, a field of white
    crosses, helmets, and red poppies."""
    _vg(d, 0, 0, w, h, (240, 180, 110), (200, 110, 60))
    d.ellipse([w * 0.78, h * 0.10, w * 0.92, h * 0.30], fill=(255, 240, 180))
    d.rectangle([0, h * 0.62, w, h], fill=(90, 110, 60))
    d.rectangle([0, h * 0.62, w, h * 0.66], fill=(70, 90, 50))
    for cx, cy, sc in ((0.12, 0.72, 1.0), (0.28, 0.68, 0.9),
                       (0.44, 0.74, 1.1), (0.60, 0.70, 0.9),
                       (0.76, 0.75, 1.0), (0.90, 0.70, 0.85)):
        cw = w * 0.03 * sc
        d.rectangle([w * cx - cw / 2, h * cy, w * cx + cw / 2,
                     h * (cy + 0.16)], fill=(240, 240, 235))
        d.rectangle([w * cx - cw * 1.4, h * (cy + 0.04), w * cx + cw * 1.4,
                     h * (cy + 0.08)], fill=(240, 240, 235))
    for hx, hy in ((0.20, 0.86), (0.52, 0.88), (0.84, 0.86)):
        d.pieslice([w * hx - 7, h * hy - 5, w * hx + 7, h * hy + 6], 180, 360,
                   fill=(70, 90, 70))
        d.rectangle([w * hx - 7, h * hy, w * hx + 7, h * hy + 2],
                    fill=(70, 90, 70))
    for px, py in ((0.06, 0.80), (0.36, 0.84), (0.68, 0.82), (0.95, 0.84)):
        d.ellipse([w * px - 3, h * py - 3, w * px + 3, h * py + 3],
                  fill=(200, 30, 30))
        d.ellipse([w * px - 1, h * py - 1, w * px + 1, h * py + 1],
                  fill=(30, 30, 30))


def _s_justice(d, w, h):
    """Sanctions / genocide ruling: courtroom bench, gavel, scales
    of justice, and two flags."""
    _vg(d, 0, 0, w, h, (220, 210, 190), (200, 185, 160))
    d.rectangle([0, h * 0.55, w, h], fill=(120, 80, 45))
    d.rectangle([w * 0.08, h * 0.42, w * 0.92, h * 0.58], fill=(90, 60, 35))
    d.rectangle([w * 0.08, h * 0.42, w * 0.92, h * 0.46], fill=(140, 100, 60))
    # scales of justice, centred on the bench
    d.line([(w * 0.5, h * 0.10), (w * 0.5, h * 0.40)], fill=(200, 170, 60),
           width=3)
    d.line([(w * 0.36, h * 0.14), (w * 0.64, h * 0.14)], fill=(200, 170, 60),
           width=3)
    for cx in (0.36, 0.64):
        d.line([(w * cx, h * 0.14), (w * cx - 0.05, h * 0.26)],
               fill=(200, 170, 60), width=2)
        d.line([(w * cx, h * 0.14), (w * cx + 0.05, h * 0.26)],
               fill=(200, 170, 60), width=2)
        d.pieslice([w * (cx - 0.05), h * 0.24, w * (cx + 0.05), h * 0.32],
                   0, 180, fill=(230, 200, 90))
    d.ellipse([w * 0.48, h * 0.08, w * 0.52, h * 0.12], fill=(230, 200, 90))
    # gavel on the bench, left
    d.rectangle([w * 0.14, h * 0.50, w * 0.28, h * 0.54], fill=(70, 45, 25))
    d.line([(w * 0.21, h * 0.52), (w * 0.30, h * 0.47)], fill=(90, 60, 30),
           width=3)
    # flags, right and left
    for fx, col in ((0.84, (200, 40, 40)), (0.10, (40, 90, 170))):
        d.line([(w * fx, h * 0.55), (w * fx, h * 0.20)], fill=(100, 80, 60),
               width=2)
        d.rectangle([w * fx, h * 0.20, w * (fx + 0.10), h * 0.32], fill=col)


def _s_chip(d, w, h):
    """Nvidia chip: dark circuit board, gold traces, a big green
    chip with pins, and a rising arrow."""
    _vg(d, 0, 0, w, h, (20, 60, 40), (10, 35, 25))
    for y in (0.12, 0.30, 0.68, 0.86):
        d.line([(0, h * y), (w, h * y)], fill=(40, 120, 80), width=1)
        for x in range(6):
            d.line([(w * (0.05 + x * 0.16), h * y),
                    (w * (0.05 + x * 0.16), h * (y + 0.08))],
                   fill=(40, 120, 80), width=1)
    d.rectangle([w * 0.30, h * 0.28, w * 0.70, h * 0.68], fill=(30, 130, 70))
    d.rectangle([w * 0.30, h * 0.28, w * 0.70, h * 0.68],
                outline=(120, 220, 150), width=2)
    for x in range(5):
        d.rectangle([w * (0.34 + x * 0.07), h * 0.22, w * (0.38 + x * 0.07),
                     h * 0.28], fill=(200, 200, 200))
        d.rectangle([w * (0.34 + x * 0.07), h * 0.68, w * (0.38 + x * 0.07),
                     h * 0.74], fill=(200, 200, 200))
    d.rectangle([w * 0.40, h * 0.36, w * 0.60, h * 0.60], fill=(20, 90, 50))
    d.text((w * 0.5, h * 0.48), "AI", font=sans(13, bold=True),
           fill=(255, 255, 255), anchor="mm")
    pts = [(w * 0.08, h * 0.78), (w * 0.16, h * 0.72), (w * 0.22, h * 0.74),
           (w * 0.32, h * 0.60)]
    d.line(pts, fill=(255, 255, 255), width=4, joint="curve")
    d.line(pts, fill=(60, 220, 120), width=2, joint="curve")
    d.polygon([(w * 0.32, h * 0.60), (w * 0.27, h * 0.58),
               (w * 0.30, h * 0.65)], fill=(60, 220, 120))


def _s_clinic(d, w, h):
    """Ebola clinic in the forest: green canopy, a white medical
    tent with a red cross, a stretcher, and a masked health worker."""
    _vg(d, 0, 0, w, h, (120, 180, 110), (200, 220, 170))
    for x in (0.04, 0.20, 0.80, 0.94):
        d.ellipse([w * x, h * 0.05, w * (x + 0.10), h * 0.22],
                  fill=(50, 120, 60))
        d.rectangle([w * (x + 0.04), h * 0.20, w * (x + 0.06), h * 0.34],
                    fill=(90, 70, 45))
    d.rectangle([0, h * 0.62, w, h], fill=(140, 120, 80))
    # white tent with red cross
    d.polygon([(w * 0.18, h * 0.66), (w * 0.50, h * 0.30),
               (w * 0.82, h * 0.66)], fill=(245, 245, 240))
    d.polygon([(w * 0.18, h * 0.66), (w * 0.50, h * 0.30),
               (w * 0.82, h * 0.66)], outline=(180, 180, 175), width=1)
    d.rectangle([w * 0.44, h * 0.52, w * 0.56, h * 0.66], fill=(90, 70, 50))
    d.rectangle([w * 0.48, h * 0.38, w * 0.52, h * 0.48], fill=(200, 40, 40))
    d.rectangle([w * 0.45, h * 0.41, w * 0.55, h * 0.45], fill=(200, 40, 40))
    # stretcher + masked worker in white
    d.rectangle([w * 0.06, h * 0.80, w * 0.30, h * 0.84], fill=(200, 200, 190))
    d.line([(w * 0.08, h * 0.84), (w * 0.08, h * 0.92)], fill=(60, 60, 60),
           width=2)
    d.line([(w * 0.28, h * 0.84), (w * 0.28, h * 0.92)], fill=(60, 60, 60),
           width=2)
    d.ellipse([w * 0.10, h * 0.76, w * 0.26, h * 0.80], fill=(240, 120, 40))
    d.ellipse([w * 0.86, h * 0.72, w * 0.90, h * 0.78], fill=(240, 210, 170))
    d.rectangle([w * 0.84, h * 0.78, w * 0.92, h * 0.92], fill=(245, 245, 240))
    d.rectangle([w * 0.86, h * 0.74, w * 0.90, h * 0.77], fill=(120, 200, 220))


def _s_grok(d, w, h):
    """Grok sued: a smartphone with chat bubbles, a judge's gavel
    and a courthouse column behind it."""
    _vg(d, 0, 0, w, h, (200, 215, 235), (170, 190, 215))
    d.rectangle([w * 0.06, h * 0.30, w * 0.16, h * 0.90], fill=(240, 240, 235))
    d.rectangle([w * 0.84, h * 0.30, w * 0.94, h * 0.90], fill=(240, 240, 235))
    d.rectangle([w * 0.04, h * 0.24, w * 0.18, h * 0.30], fill=(230, 230, 225))
    d.rectangle([w * 0.82, h * 0.24, w * 0.96, h * 0.30], fill=(230, 230, 225))
    # phone
    d.rounded_rectangle([w * 0.30, h * 0.14, w * 0.70, h * 0.92], radius=6,
                        fill=(30, 30, 36), outline=(10, 10, 14), width=2)
    d.rounded_rectangle([w * 0.33, h * 0.18, w * 0.67, h * 0.86], radius=4,
                        fill=(245, 245, 250))
    d.rounded_rectangle([w * 0.36, h * 0.22, w * 0.64, h * 0.38], radius=4,
                        fill=(60, 120, 200))
    d.text((w * 0.5, h * 0.30), "AI", font=sans(11, bold=True),
           fill=(255, 255, 255), anchor="mm")
    d.rounded_rectangle([w * 0.36, h * 0.44, w * 0.60, h * 0.54], radius=4,
                        fill=(220, 225, 235))
    d.rounded_rectangle([w * 0.40, h * 0.58, w * 0.64, h * 0.68], radius=4,
                        fill=(200, 230, 200))
    d.line([(w * 0.36, h * 0.74), (w * 0.64, h * 0.74)], fill=(180, 180, 180),
           width=2)
    # gavel, lower right
    d.rectangle([w * 0.72, h * 0.78, w * 0.86, h * 0.83], fill=(70, 45, 25))
    d.line([(w * 0.79, h * 0.80), (w * 0.88, h * 0.74)], fill=(90, 60, 30),
           width=3)


def _s_pharma(d, w, h):
    """Sanofi deal: bright lab bench, a pill bottle, capsules and
    a flask, with a gold $ badge."""
    _vg(d, 0, 0, w, h, (235, 245, 250), (200, 220, 230))
    d.rectangle([0, h * 0.68, w, h], fill=(120, 170, 190))
    d.rectangle([0, h * 0.68, w, h * 0.72], fill=(90, 140, 160))
    # pill bottle
    d.rectangle([w * 0.10, h * 0.30, w * 0.34, h * 0.68], fill=(255, 255, 255))
    d.rectangle([w * 0.10, h * 0.30, w * 0.34, h * 0.68],
                outline=(150, 160, 170), width=1)
    d.rectangle([w * 0.13, h * 0.22, w * 0.31, h * 0.30], fill=(30, 120, 180))
    d.rectangle([w * 0.13, h * 0.44, w * 0.31, h * 0.58], fill=(230, 240, 250))
    d.line([(w * 0.15, h * 0.48), (w * 0.29, h * 0.48)], fill=(30, 120, 180),
           width=1)
    d.line([(w * 0.15, h * 0.53), (w * 0.27, h * 0.53)], fill=(30, 120, 180),
           width=1)
    # capsules
    for cx, cy, col in ((0.52, 0.76, (200, 60, 60)), (0.66, 0.82, (240, 180, 60)),
                        (0.58, 0.88, (60, 140, 200))):
        d.ellipse([w * cx - 9, h * cy - 4, w * cx + 9, h * cy + 4], fill=col)
        d.ellipse([w * cx - 9, h * cy - 4, w * cx, h * cy + 4],
                  fill=(255, 255, 255))
    # flask
    d.rectangle([w * 0.76, h * 0.30, w * 0.82, h * 0.48], fill=(200, 220, 230))
    d.polygon([(w * 0.72, h * 0.48), (w * 0.86, h * 0.48),
               (w * 0.92, h * 0.68), (w * 0.66, h * 0.68)],
              fill=(200, 220, 230))
    d.polygon([(w * 0.70, h * 0.56), (w * 0.88, h * 0.56),
               (w * 0.90, h * 0.68), (w * 0.68, h * 0.68)],
              fill=(90, 180, 120))
    # gold $ badge
    d.ellipse([w * 0.84, h * 0.06, w * 0.98, h * 0.24], fill=(240, 190, 60))
    d.ellipse([w * 0.84, h * 0.06, w * 0.98, h * 0.24],
              outline=(180, 130, 30), width=1)
    d.text((w * 0.91, h * 0.15), "$", font=sans(11, bold=True),
           fill=(255, 255, 255), anchor="mm")


SCENE_SMALL = {
    "capitol": _s_capitol, "oil": _s_oil, "warship": _s_warship,
    "desert": _s_desert, "talks": _s_talks, "volcano": _s_volcano,
    "rugby": _s_rugby, "football": _s_football, "nhs": _s_nhs,
    "quake": _s_quake, "space": _s_space, "memorial": _s_memorial,
    "justice": _s_justice, "chip": _s_chip, "clinic": _s_clinic,
    "grok": _s_grok, "pharma": _s_pharma, "cop31": _scene_cop31,
}

# ---------------------------------------------------------------- blue-sea map
# Real lon/lat outlines, equirectangular, lon -180..180, lat 78..-56,
# pale-green polygons on a blue sea with a light graticule and a dark
# ink outline around each landmass.
NORTH_AMERICA = [(-168, 66), (-140, 70), (-125, 72), (-110, 68), (-95, 69),
                 (-85, 66), (-80, 73), (-65, 62), (-55, 52), (-60, 47),
                 (-70, 42), (-75, 35), (-80, 32), (-85, 29), (-90, 21),
                 (-97, 16), (-105, 20), (-115, 28), (-125, 40), (-125, 49),
                 (-140, 60), (-155, 58), (-165, 60)]
SOUTH_AMERICA = [(-80, 9), (-75, 11), (-62, 9), (-52, 5), (-50, 0),
                 (-44, -3), (-35, -8), (-40, -20), (-48, -28), (-57, -38),
                 (-65, -45), (-70, -54), (-73, -50), (-73, -37), (-70, -20),
                 (-80, -5)]
AFRICA = [(-17, 15), (-10, 31), (-5, 35), (10, 37), (20, 32), (32, 31),
          (35, 28), (43, 12), (51, 11), (48, 0), (40, -10), (35, -18),
          (32, -29), (26, -34), (19, -35), (15, -27), (12, -18), (9, 4),
          (-8, 4)]
EURASIA = [(-10, 36), (-9, 43), (-2, 48), (0, 50), (5, 58), (8, 57),
           (18, 56), (21, 55), (24, 59), (28, 60), (30, 70), (40, 68),
           (55, 69), (70, 73), (90, 75), (110, 74), (130, 72), (150, 70),
           (170, 66), (178, 65), (170, 60), (162, 56), (158, 52),
           (142, 50), (140, 40), (135, 35), (130, 32), (127, 35),
           (122, 38), (120, 32), (115, 23), (108, 18), (105, 9), (100, 8),
           (98, 12), (95, 16), (92, 21), (88, 22), (80, 13), (77, 8),
           (72, 20), (66, 25), (60, 25), (57, 26), (52, 28), (48, 30),
           (44, 29), (40, 32), (36, 36), (30, 36), (27, 40), (23, 40),
           (19, 42), (12, 44), (8, 44), (3, 43), (-2, 37), (-9, 37)]
AUSTRALIA = [(113, -22), (114, -32), (120, -34), (130, -32), (140, -38),
             (147, -39), (150, -37), (153, -27), (146, -19), (142, -11),
             (136, -12), (132, -12), (126, -14), (122, -17)]
UNITED_KINGDOM = [(-5, 50), (-3, 53), (-5, 56), (-2, 58), (0, 53)]
JAPAN = [(130, 31), (133, 34), (137, 35), (140, 38), (141, 42), (143, 44),
         (140, 40)]
NEW_ZEALAND = [(167, -45), (172, -41), (175, -38), (178, -37), (174, -41)]
LAND = [NORTH_AMERICA, SOUTH_AMERICA, AFRICA, EURASIA, AUSTRALIA,
        UNITED_KINGDOM, JAPAN, NEW_ZEALAND]

# (story number, lon, lat, region, leader offset in px). Offsets keep
# crowded pins apart: 5 (Saudi oil) and 6 (Benghazi) sit close
# together in the Gulf, and 12 (Britain) sits on top of 11
# (Liverpool); their pins are nudged away with a leader line back
# to the true spot, marked by a small dot. v17: pin 10 moves from
# Turin to South Africa (the Springboks story).
PINS = [
    (1, 56.5, 26.6, "MIDDLE EAST", 12, 10),   # Strait of Hormuz
    (2, 35.2, 47.8, "EUROPE", 0, 0),          # Zaporizhzhia
    (3, 34.5, 31.5, "MIDDLE EAST", 12, -12),  # Gaza City
    (4, 13.4, 52.5, "EUROPE", 0, 0),          # Berlin
    (5, 37.6, 55.8, "EUROPE", -16, -10),      # Moscow (war toll)
    (6, 20.0, 32.0, "MIDDLE EAST", 0, 0),     # Benghazi
    (7, -0.1, 51.5, "EUROPE", -14, -14),      # London
    (8, -122.0, 37.4, "TECH & BUSINESS", 0, 0),  # Santa Clara
    (9, 30.7, 36.9, "EUROPE", 10, 12),        # Antalya
    (10, 29.5, 1.5, "SCIENCE & CULTURE", 0, 0),  # Ituri
    (11, 85.3, 28.0, "ASIA-PACIFIC", 0, 0),   # Nepal
    (12, -77.0, 39.0, "AMERICAS", 0, 0),      # Washington
    (13, 2.35, 48.85, "EUROPE", 18, 10),      # Paris
]
PIN_R = 5


def draw_map(d, x0, y0, x1, y1):
    """Blue-sea world map (equirectangular, lon -180..180, lat 78..-56)."""
    d.rectangle([x0, y0, x1, y1], fill=SEA)
    mw, mh = x1 - x0, y1 - y0

    def X(lon):
        return x0 + (lon + 180.0) / 360.0 * mw

    def Y(lat):
        return y0 + (78.0 - lat) / 134.0 * mh

    for lon in range(-150, 181, 30):
        d.line([(X(lon), y0), (X(lon), y1)], fill=SEAGRID, width=1)
    for lat in (-30, 0, 30, 60):
        d.line([(x0, Y(lat)), (x1, Y(lat))], fill=SEAGRID, width=1)
    for poly in LAND:
        pts = [(X(lon), Y(lat)) for lon, lat in poly]
        d.polygon(pts, fill=LANDC)
        d.line(pts + [pts[0]], fill=INK, width=2, joint="curve")
    for num, lon, lat, region, dx, dy in PINS:
        px, py = X(lon), Y(lat)
        cx, cy = px + dx, py + dy
        if dx or dy:
            d.line([(px, py), (cx, cy)], fill=INK, width=1)
            d.ellipse([px - 2, py - 2, px + 2, py + 2],
                      fill=REGION_COLOUR[region])
        r = PIN_R
        d.ellipse([cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2],
                  fill=(255, 255, 255))
        d.ellipse([cx - r, cy - r, cx + r, cy + r],
                  fill=REGION_COLOUR[region], outline=(255, 255, 255),
                  width=1)
        d.text((cx, cy), str(num), font=sans(8, bold=True),
               fill=(255, 255, 255), anchor="mm")


def draw_clipped(img, fn, box):
    """Paint scene fn on its own layer exactly box-sized, then paste.

    The v14 clip backstop: no part of any drawing (smoke, flame,
    sun, moon, floodlights, ash) can ever escape its picture box,
    because the layer is the box's size. The offending shapes were
    also moved or shrunk to sit whole inside their boxes, so the
    clip is a backstop rather than a visible cut.
    """
    x0, y0, x1, y1 = box
    layer = Image.new("RGB", (x1 - x0, y1 - y0), (255, 255, 255))
    fn(ImageDraw.Draw(layer), x1 - x0, y1 - y0)
    img.paste(layer, (x0, y0))

# ---------------------------------------------------------------- build
FOOTER_LEFT = ("Sources: Reuters, BBC, AP, Kyiv Ind., RFE/RL, IQMIA, "
               "UN News, Oxfam, WSJ, NYT, The Hill, Politico, Horizon, "
               "Principia \u2014 24 Nov 2026")
FOOTER_RIGHT = ("THE WORLD IN ONE DAY \u2014 TUESDAY 24 NOVEMBER 2026 "
                "\u00b7 ONE PAGE")

def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    trimmed = []       # headlines that had to be trimmed (must stay empty)
    list_widths = []   # (number, width, column limit) for the one-line check
    card_gaps = []     # (number, lines, headline->location ink gap,
                       #  location ink->border gap, headline top offset)
    hero_lines = []    # (number, title line count) - must be 2 each
    hero_deck_lines = []  # (number, deck line count) - must be 2 each
    dc_widths = []     # DATE CHECK body line widths
    dc_lefts = []      # DATE CHECK body line ink left edges - must be one
                       # straight vertical line (v20 left alignment)
    loc_checks = []    # (number, region, location text bbox) for the
                       # v17 colour probe: the location ink must be
                       # its region colour, never the old grey

    # navy masthead band
    d.rectangle([0, 0, W, 26], fill=NAVY)
    d.text((24, 13), "THE WORLD IN ONE DAY", font=sans(13, bold=True),
           fill=(255, 255, 255), anchor="lm")
    d.text((1000, 13),
           "35 STORIES \u00b7 6 REGIONS \u00b7 EVERY ONE DATED TUESDAY 24 NOVEMBER 2026",
           font=sans(11, bold=True), fill=(255, 255, 255), anchor="rm")

    # date headline: centred, giant serif bold
    d.text((512, 32), "Tuesday 24 November 2026", font=serif(58, bold=True),
           fill=INK, anchor="ma")
    d.text((512, 100),
           "Three tankers hit mines \u00b7 Russian strike kills 2, wounds 40 "
           "\u00b7 Israeli strikes kill Hamas security chief",
           font=serif(16, italic=True), fill=RED, anchor="ma")

    # numbers strip
    strip_y, strip_h = 126, 40
    cell_w = 976 / 6
    f_num = serif(24, bold=True)
    f_lab = sans(9)
    d.line([(24, strip_y), (1000, strip_y)], fill=LINE, width=1)
    for i, (num, label) in enumerate(NUMBERS):
        cx = 24 + cell_w * (i + 0.5)
        d.text((cx, strip_y + 2), num, font=f_num, fill=RED, anchor="ma")
        d.text((cx, strip_y + 28), label, font=f_lab, fill=INK_SOFT,
               anchor="ma")
        if i:
            x = 24 + cell_w * i
            d.line([(x, strip_y + 4), (x, strip_y + strip_h - 2)],
                   fill=(200, 190, 165), width=1)
    d.line([(24, strip_y + strip_h), (1000, strip_y + strip_h)],
           fill=LINE, width=1)

    # region colour bar. v1 widths (976 px total): EUROPE 170,
    # MIDDLE EAST 150, ASIA-PACIFIC 180, AMERICAS 140,
    # TECH & BUSINESS 160, SCIENCE & CULTURE 176 - the two
    # longest labels ("SCIENCE & CULTURE 2", 135.8 px at 11 pt
    # bold) need the widest cells.
    bar_y, bar_h = 170, 22
    x = 24
    widths = {"EUROPE": 170, "MIDDLE EAST": 150, "ASIA-PACIFIC": 180,
              "AMERICAS": 140, "TECH & BUSINESS": 160,
              "SCIENCE & CULTURE": 176}
    for name, count, colour in REGIONS:
        w = widths[name]
        d.rectangle([x, bar_y, x + w - 1, bar_y + bar_h], fill=colour)
        d.text((x + w / 2, bar_y + bar_h / 2), f"{name} {count}",
               font=sans(11, bold=True), fill=(255, 255, 255), anchor="mm")
        x += w

    # three hero cards: 26 pt titles, all exactly 2 lines; decks
    # also exactly 2 lines each (v20: hero #3's deck grows to two
    # lines so it matches heroes #1 and #2).
    hero_w, hero_gap = 314, 17
    f_kick = sans(10, bold=True)
    f_hl = serif(HERO_TITLE_PT, bold=True)
    f_deck = sans(10)
    f_cap = sans(9, bold=True)
    for i, hero in enumerate(HEROES):
        x0 = 24 + i * (hero_w + hero_gap)
        x1 = x0 + hero_w
        y1 = HERO_Y + HERO_H
        d.rectangle([x0, HERO_Y, x1, y1], outline=INK, width=1, fill=CARD)
        draw_clipped(img, SCENE_HERO[hero["scene"]],
                     (x0 + 1, HERO_Y + 1, x1 - 1, HERO_Y + HERO_SCENE_H))
        d.rectangle([x0, HERO_Y + HERO_SCENE_H, x1,
                     HERO_Y + HERO_SCENE_H + 16], fill=INK)
        d.text((x0 + 8, HERO_Y + HERO_SCENE_H + 8), hero["caption"],
               font=f_cap, fill=(255, 255, 255), anchor="lm")
        d.text((x0 + 8, HERO_Y + HERO_SCENE_H + 22), hero["kicker"],
               font=f_kick, fill=RED)
        num_badge(d, x1 - 14, HERO_Y + HERO_SCENE_H + 27, hero["num"], r=10)
        lines, trim = fit_lines(d, hero["title"], f_hl, hero_w - 16, 2)
        if trim:
            trimmed.append(("hero", hero["num"]))
        hero_lines.append((hero["num"], len(lines)))
        for li, line in enumerate(lines):
            d.text((x0 + 8, HERO_Y + HERO_SCENE_H + 36 + li * HERO_TITLE_LEAD),
                   line, font=f_hl, fill=INK)
        deck, trim = fit_lines(d, hero["deck"], f_deck, hero_w - 16, 2)
        if trim:
            trimmed.append(("hero-deck", hero["num"]))
        hero_deck_lines.append((hero["num"], len(deck)))
        for li, line in enumerate(deck):
            d.text((x0 + 8, HERO_Y + HERO_SCENE_H + HERO_DECK_OFF + li * 12),
                   line, font=f_deck, fill=INK_SOFT)

    # ten small cards, two rows of five: picture 70 px, headline
    # starting at the SAME y in every card (picture + 4 px), 12 pt
    # bold on a 13 px leading, max 3 lines, left aligned. Bottom
    # row flush to the card's bottom edge: location (9 pt BOLD,
    # v17: in its place's region colour) bottom-left, badge (r=7,
    # 9 pt number) bottom-right, both centred on a row 8 px above
    # the bottom edge.
    f_scap = sans(CARD_HEAD_PT, bold=True)
    f_sloc = sans(CARD_LOC_PT, bold=True)
    card_w, card_gap = 187, 10
    for idx, story in enumerate(SMALL):
        row, col = divmod(idx, 5)
        x0 = 24 + col * (card_w + card_gap)
        x1 = x0 + card_w
        y0 = CARD_Y0 + row * CARD_PITCH
        y1 = y0 + CARD_H
        d.rectangle([x0, y0, x1, y1], outline=INK, width=1, fill=CARD)
        draw_clipped(img, SCENE_SMALL[story["scene"]],
                     (x0 + 1, y0 + 1, x1 - 1, y0 + CARD_PIC_H))
        lab_w = d.textlength(story["label"], font=sans(8, bold=True)) + 12
        d.rectangle([x0 + 1, y0 + 1, x0 + 1 + lab_w, y0 + 14], fill=RED)
        d.text((x0 + 7, y0 + 8), story["label"], font=sans(8, bold=True),
               fill=(255, 255, 255), anchor="lm")
        lines, trim = fit_lines(d, story["cap"], f_scap, card_w - 12, 3)
        if trim:
            trimmed.append(("card", story["num"]))
        n = len(lines)
        ty = y0 + CARD_PIC_H + CARD_HEAD_GAP
        for li, line in enumerate(lines):
            d.text((x0 + 6, ty + li * CARD_HEAD_LEAD), line,
                   font=f_scap, fill=INK)
        loc_y = y1 - CARD_BOTTOM_ROW
        loc_col = REGION_COLOUR[story["region"]]
        d.text((x0 + 6, loc_y), story["loc"], font=f_sloc,
               fill=loc_col, anchor="lm")
        num_badge(d, x1 - 12, loc_y, story["num"], r=CARD_BADGE_R,
                  pt=CARD_BADGE_PT)
        last_top = ty + (n - 1) * CARD_HEAD_LEAD
        hb = d.textbbox((x0 + 6, last_top), lines[-1], font=f_scap)
        lb = d.textbbox((x0 + 6, loc_y), story["loc"], font=f_sloc,
                        anchor="lm")
        gap = lb[1] - hb[3]
        loc_gap = y1 - lb[3]
        badge_left = x1 - 12 - CARD_BADGE_R
        assert lb[2] < badge_left, \
            f"card {story['num']}: location runs into badge"
        card_gaps.append((story["num"], n, gap, loc_gap, ty - y0))
        loc_checks.append((story["num"], story["region"], lb))

    # bottom: blue-sea map (left) + numbered list (right). v20
    # restores v18's layout here (v19's 12 px compression is
    # undone, since the DATE CHECK box is compact again): the rule
    # under the right-hand header sits at BOTTOM_HDR_Y+20, the
    # list starts at LIST_Y0=724 and ends at 918, and the map
    # outline bottom is 927 with MAP_BOX (30, 730, 354, 921) -
    # 191 px tall. The map's top stays at MAP_Y0=724 so the
    # subline ink (ends y=722) keeps its 2 px gap, and the DATE
    # CHECK top is back at 930, leaving a 12 px gap under the
    # list and a 3 px gap under the map.
    d.text((24, BOTTOM_HDR_Y), "WHERE IT HAPPENED",
           font=sans(11, bold=True), fill=INK)
    d.text((24, BOTTOM_HDR_Y + 13), "pins match story numbers",
           font=sans(9), fill=INK_SOFT)
    d.text((372, BOTTOM_HDR_Y), "ALSO ON TUESDAY 24 NOVEMBER",
           font=sans(12, bold=True), fill=INK)
    d.line([(372, BOTTOM_HDR_Y + 20), (1000, BOTTOM_HDR_Y + 20)],
           fill=LINE, width=1)
    d.rectangle([24, MAP_Y0, 360, MAP_BOTTOM], outline=INK, width=1,
                fill=CARD)
    draw_map(d, *MAP_BOX)

    # every list item on exactly one line; the number wears its
    # region's colour, the source follows the headline in grey.
    # Left column allows 300 px, right column 288 px.
    f_item = sans(LIST_PT)
    f_inum = sans(LIST_NUM_PT, bold=True)
    col_x = [372, 692]
    col_limit = [300, 288]
    for ci, items in enumerate((LIST[:11], LIST[11:])):
        x = col_x[ci]
        y = LIST_Y0
        for num, headline, source in items:
            d.text((x, y), str(num), font=f_inum,
                   fill=REGION_COLOUR[LIST_REGION[num]])
            line = f"{headline} ({source})"
            w = d.textlength(line, font=f_item)
            list_widths.append((num, w, col_limit[ci]))
            d.text((x + 20, y), line, font=f_item, fill=INK)
            y += LIST_STEP

    # DATE CHECK box (v21: 62 px tall, to fit exactly three body
    # lines, compact): a red band fills the whole left side of
    # the box - a vertical red column, full height of the box,
    # its left edge the box's own left border, 115 px wide.
    # "DATE CHECK" sits centred horizontally and vertically inside
    # the band (one line, 77 px at 11 pt bold). The body is 3
    # hard-coded lines to the right of the band, vertically
    # centred in the box, LEFT-ALIGNED: every line starts at
    # DC_BODY_X = 154 (15 px after the band edge), so the left
    # edges form one straight vertical line. The band is drawn
    # from the outer corner, then both red borders are redrawn
    # over it, so the borders stay crisp and no cream gap remains
    # between the red and the border.
    bx0, by0, bx1, by1 = DC_BOX
    d.rectangle([bx0, by0, bx1, by1], outline=RED, width=2, fill=CARD)
    d.rectangle([bx0 + 4, by0 + 4, bx1 - 4, by1 - 4], outline=RED, width=1)
    d.rectangle([bx0, by0, bx0 + DC_BAND_W, by1], fill=RED)
    d.rectangle([bx0, by0, bx1, by1], outline=RED, width=2)
    d.rectangle([bx0 + 4, by0 + 4, bx1 - 4, by1 - 4], outline=RED, width=1)
    d.text((bx0 + DC_BAND_W / 2, (by0 + by1) / 2), "DATE CHECK",
           font=sans(11, bold=True), fill=(255, 255, 255), anchor="mm")
    for li, line in enumerate(DC_BODY):
        w = d.textlength(line, font=sans(10))
        dc_widths.append(w)
        d.text((DC_BODY_X, DC_BODY_Y0 + li * DC_BODY_LEAD), line,
               font=sans(10), fill=INK)
        bb = d.textbbox((DC_BODY_X, DC_BODY_Y0 + li * DC_BODY_LEAD),
                        line, font=sans(10))
        dc_lefts.append(bb[0])

    # footer strip. v16: the source list gains Al Jazeera (the
    # Belgium strike); WSJ and The Times drop out, since no story
    # v1: the footer names the outlets cited on the page
    # (Reuters, BBC, AP, Kyiv Ind., RFE/RL, IQMIA, UN News,
    # Oxfam, WSJ, NYT, The Hill, Politico, Horizon, Principia);
    # Meduza, Mediazona, 10Things and Medium are cited in
    # README.md. The line is set at 9 pt so it still ends well
    # clear of the right-hand footer text.
    d.text((24, 1000), FOOTER_LEFT, font=sans(9), fill=INK_SOFT)
    d.text((1000, 1000), FOOTER_RIGHT, font=sans(9, bold=True),
           fill=INK, anchor="ra")

    return img, trimmed, list_widths, card_gaps, hero_lines, \
        hero_deck_lines, dc_widths, dc_lefts, loc_checks

def main():
    out_dir = (os.environ.get("MAKEFUN_OUTPUT_DIR")
               or os.environ.get("OUTPUT_DIR") or "/output")
    try:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        probe = Path(out_dir) / ".write_test"
        probe.write_text("ok")
        probe.unlink()
    except OSError:
        out_dir = str(Path(__file__).resolve().parent)
    img, trimmed, list_widths, card_gaps, hero_lines, hero_deck_lines, \
        dc_widths, dc_lefts, loc_checks = build()
    out_path = Path(out_dir) / "entry.png"
    img.save(out_path, format="PNG")
    digest = hashlib.sha256(out_path.read_bytes()).hexdigest()
    print(f"wrote {out_path}  {img.size[0]}x{img.size[1]}  "
          f"{out_path.stat().st_size} bytes  sha256={digest}")
    print(f"stories: {TOTAL_STORIES}")
    print(f"heroes: {HERO_H} px tall, scene {HERO_SCENE_H} px, "
          f"title {HERO_TITLE_PT} pt")
    print(f"cards: {CARD_H} px tall, pitch {CARD_PITCH}, "
          f"picture {CARD_PIC_H} px")
    print(f"list step: {LIST_STEP} px, bottom headers at y={BOTTOM_HDR_Y}")
    assert not trimmed, f"trimmed headlines: {trimmed}"
    print(f"trimmed headlines: {trimmed if trimmed else 'none'}")
    over = [(n, w, lim) for n, w, lim in list_widths if w > lim]
    assert not over, f"list lines over column limit: {over}"
    widest = max(list_widths, key=lambda t: t[1] - t[2])
    print(f"widest list line: #{widest[0]} {widest[1]:.1f} px "
          f"(limit {widest[2]} px)")
    print(f"list lines over their column limit: {over if over else 'none'}")
    print(f"last list item ends at y={LIST_Y0 + 10 * LIST_STEP + 14} "
          f"(DATE CHECK top 930)")
    assert LIST_NUM_PT < LIST_PT, "list numbers must be smaller than text"
    probe_d = ImageDraw.Draw(img)
    num_w = probe_d.textlength("35", font=sans(LIST_NUM_PT, bold=True))
    assert num_w < 20, f"widest list number {num_w:.1f} px overflows gutter"
    print(f"widest list number: {num_w:.1f} px (gutter 20 px)")
    assert LIST_STEP > 14, f"list step {LIST_STEP} px leaves no gap"
    print(f"list line gap: {LIST_STEP - 14} px between 11 pt lines")
    assert LIST_Y0 + 10 * LIST_STEP + 14 <= 930, "list runs into DATE CHECK"
    assert BOTTOM_HDR_Y > 678 and LIST_STEP < 20, "bottom block not shifted"
    mx0, my0, mx1, my1 = MAP_BOX
    mw, mh = mx1 - mx0, my1 - my0
    pts = []
    for num, lon, lat, region, dx, dy in PINS:
        px = mx0 + (lon + 180.0) / 360.0 * mw + dx
        py = my0 + (78.0 - lat) / 134.0 * mh + dy
        pts.append((num, px, py))
    best = (1e9, None)
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            dd = ((pts[i][1] - pts[j][1]) ** 2 +
                  (pts[i][2] - pts[j][2]) ** 2) ** 0.5
            if dd < best[0]:
                best = (dd, (pts[i][0], pts[j][0]))
    print(f"closest pins: {best[1]} at {best[0]:.1f} px "
          f"(pin diameter {2 * PIN_R + 4})")
    assert best[0] > 2 * PIN_R + 4, "closest pins overlap"
    print(f"hero title lines: {hero_lines}")
    assert all(n == 2 for _, n in hero_lines), \
        f"hero titles not all 2 lines: {hero_lines}"
    print(f"hero deck lines: {hero_deck_lines}")
    assert all(n == 2 for _, n in hero_deck_lines), \
        f"hero decks not all 2 lines: {hero_deck_lines}"
    print("card gaps (headline->location ink, location ink->border):")
    for num, n, gap, loc_gap, _ty in card_gaps:
        print(f"  #{num}: {n} lines, gap {gap} px, border gap {loc_gap} px")
    assert all(g >= 3 for _, _, g, _, _ in card_gaps), \
        "headline too close to location line"
    assert all(3 <= lg <= 6 for _, _, _, lg, _ in card_gaps), \
        "location not flush to the card border"
    print("card location colours (v17 - by place's region):")
    px = img.load()
    for num, region, lb in loc_checks:
        col = REGION_COLOUR[region]
        hits = sum(1 for yy in range(lb[1], lb[3] + 1)
                   for xx in range(lb[0], lb[2] + 1)
                   if px[xx, yy] == col)
        grey = sum(1 for yy in range(lb[1], lb[3] + 1)
                   for xx in range(lb[0], lb[2] + 1)
                   if px[xx, yy] == INK_SOFT)
        print(f"  #{num} {region}: {hits} px in {col}, grey {grey} px")
        assert hits >= 20, \
            f"card {num}: location not in its region colour {col}"
        assert grey == 0, \
            f"card {num}: location still has grey pixels"
    bx0, by0, bx1, by1 = DC_BOX
    assert by1 - by0 == 62, \
        f"DATE CHECK box height is {by1 - by0} px, not 62"
    assert by1 <= 996, \
        f"DATE CHECK box bottom {by1} runs into the footer at y=1000"
    assert DC_BAND_W == 115, "DATE CHECK band width changed"
    assert len(DC_BODY) == 3, \
        f"DATE CHECK body is {len(DC_BODY)} lines, not 3"
    # v1 revised: the nine exclusions must be present - the
    # original four (COP31 collapse 23 Nov, ICJ Rohingya ruling
    # Thu 19 Nov, 700,000 tally 23 Nov, Hormuz blockade
    # 13 Apr / 14 Jul) plus the five added from v21 (Shenzhen
    # 19 Nov, Kerch Bridge 16-17 Nov, Poland missiles 20 Nov,
    # FBI hack 20 Nov, Alcaraz win 22 Nov). Nine items means
    # eight ";" separators plus one more ";" inside the Hormuz
    # item ("... are 24 Nov; the blockade is not"), nine in all.
    dc_text = " ".join(DC_BODY)
    assert "COP31 collapse (23 Nov)" in dc_text, "v1: COP31 item missing"
    assert "ICJ Rohingya genocide ruling (Thu 19 Nov)" in dc_text, \
        "v1: ICJ item missing"
    assert "700,000 tally released (23 Nov)" in dc_text, \
        "v1: tally item missing"
    assert "Hormuz blockade first imposed (13 Apr)" in dc_text, \
        "v1: blockade item missing"
    assert "reinstated (14 Jul)" in dc_text, "v1: blockade item missing"
    assert "Shenzhen (19 Nov)" in dc_text, "v1: Shenzhen item missing"
    assert "Kerch Bridge (16\u201317 Nov)" in dc_text, \
        "v1: Kerch item missing"
    assert "Poland missiles (20 Nov)" in dc_text, \
        "v1: Poland item missing"
    assert "FBI hack (20 Nov)" in dc_text, "v1: FBI item missing"
    assert "Alcaraz win (22 Nov)" in dc_text, "v1: Alcaraz item missing"
    assert dc_text.count(";") == 9, \
        f"DATE CHECK should list 9 items: {dc_text.count(';')} separators"
    assert max(dc_widths) <= 839, \
        f"DATE CHECK body line too wide: {dc_widths}"
    # v1 revised: the added exclusions fill the box, so the lines
    # must reach near the 839 px limit (the point of this change)
    # and stay balanced - v21's limits again (see module docstring).
    assert min(dc_widths) >= 750, \
        f"DATE CHECK body line too short, right side still empty: {dc_widths}"
    assert max(dc_widths) - min(dc_widths) < 70, \
        f"DATE CHECK body lines unbalanced: {dc_widths}"
    # v20: the body is LEFT-ALIGNED - all three lines must start
    # at one straight left edge (DC_BODY_X). Measure the real
    # ink left edge of each line (PIL draws from the ascender top,
    # and glyph side bearings can shift the ink by a pixel).
    assert max(dc_lefts) - min(dc_lefts) <= 1, \
        f"DATE CHECK body lines not left-aligned: left edges {dc_lefts}"
    assert all(abs(left - DC_BODY_X) <= 1 for left in dc_lefts), \
        f"DATE CHECK body left edge not at x={DC_BODY_X}: {dc_lefts}"
    # the body ink must sit centred vertically in the box with even
    # padding. PIL draws text from the ascender top, so measure the
    # real ink (the old asserts assumed y was the baseline and let
    # the text sit 9 px too low, 21 px above and 3 px below).
    ink_tops, ink_bots = [], []
    for li, line in enumerate(DC_BODY):
        bb = probe_d.textbbox((DC_BODY_X, DC_BODY_Y0 + li * DC_BODY_LEAD),
                              line, font=sans(10))
        ink_tops.append(bb[1])
        ink_bots.append(bb[3])
    top_pad = min(ink_tops) - by0
    bot_pad = by1 - max(ink_bots)
    assert top_pad >= 8 and bot_pad >= 8, \
        f"DATE CHECK body too close to the box edge: top {top_pad}, " \
        f"bottom {bot_pad}"
    assert abs(top_pad - bot_pad) <= 2, \
        f"DATE CHECK body not centred vertically: top {top_pad}, " \
        f"bottom {bot_pad}"
    longest = max(dc_widths)
    right_pad = bx1 - (DC_BODY_X + longest)
    print(f"DATE CHECK body paddings: top {top_pad} px, bottom "
          f"{bot_pad} px, left {DC_BODY_PAD} px, right {right_pad:.1f} px "
          f"(longest line)")
    print(f"DATE CHECK band: {DC_BAND_W} px wide, full height "
          f"({by1 - by0} px), label centred at "
          f"({bx0 + DC_BAND_W / 2}, {(by0 + by1) / 2})")
    print(f"DATE CHECK body: {len(DC_BODY)} lines, left-aligned at "
          f"x={DC_BODY_X}, ink left edges {dc_lefts}, widths "
          f"{[round(w, 1) for w in dc_widths]} px")
    assert px[30, 940] == RED, "DATE CHECK band interior not red"
    assert px[130, 960] == RED, "DATE CHECK band right edge not red"
    assert px[140, 960] == CARD, "DATE CHECK band leaks past its right edge"
    assert px[970, 960] == CARD, "DATE CHECK box interior not cream"
    white = sum(1 for yy in range(by0, by1)
                for xx in range(bx0, bx0 + DC_BAND_W)
                if px[xx, yy] == (255, 255, 255))
    assert white > 50, "DATE CHECK label text missing from the red band"
    print(f"DATE CHECK label white pixels in band: {white}")
    lw = probe_d.textlength(FOOTER_LEFT, font=sans(9))
    rw = probe_d.textlength(FOOTER_RIGHT, font=sans(9, bold=True))
    assert 24 + lw < 1000 - rw, "footer texts overlap"
    print(f"footer: left ends at {24 + lw:.1f}, right starts at "
          f"{1000 - rw:.1f} (gap {1000 - rw - 24 - lw:.1f} px)")
    ESCAPE = {(58, 56, 62), (70, 68, 74), (110, 108, 118),
              (120, 118, 114), (120, 116, 110), (140, 136, 130),
              (235, 90, 25), (250, 170, 40), (255, 225, 120),
              (255, 232, 150), (255, 226, 150), (255, 240, 180),
              (250, 120, 30), (255, 200, 90), (250, 140, 50)}
    boxes = []
    for i in range(3):
        x0 = 24 + i * (314 + 17)
        boxes.append((x0 + 1, HERO_Y + 1, x0 + 314 - 1,
                      HERO_Y + HERO_SCENE_H))
    for idx in range(10):
        row, col = divmod(idx, 5)
        x0 = 24 + col * (187 + 10)
        y0 = CARD_Y0 + row * CARD_PITCH
        boxes.append((x0 + 1, y0 + 1, x0 + 187 - 1, y0 + CARD_PIC_H))
    leaks = []
    for (bx0, by0, bx1, by1) in boxes:
        for yy in range(by0 - 3, by1 + 3):
            for xx in list(range(bx0 - 3, bx0)) + list(range(bx1, bx1 + 3)):
                if px[xx, yy] in ESCAPE:
                    leaks.append((xx, yy, px[xx, yy]))
        for xx in range(bx0, bx1):
            for yy in list(range(by0 - 3, by0)) + list(range(by1, by1 + 3)):
                if px[xx, yy] in ESCAPE:
                    leaks.append((xx, yy, px[xx, yy]))
    assert not leaks, f"scene elements leak outside picture boxes: {leaks[:5]}"
    print(f"smoke-clip probe: 0 leaks in the 3 px ring around "
          f"all {len(boxes)} picture boxes")
    tops = {t for _, _, _, _, t in card_gaps}
    assert len(tops) == 1, f"headline offsets differ: {sorted(tops)}"
    print(f"headline offset identical in all cards: "
          f"+{tops.pop()} px from card top")


if __name__ == "__main__":
    main()
