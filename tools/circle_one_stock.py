#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سهمٌ واحد · قاعٌ رئيسى · الرقم على الدائرة · نسبةٌ مع الكوكب.

يُنفّذ الطريقة كما فى خطاب البنّ (19 مارس 1954):

    8729 ÷ 1   = 8729  ⇒ 89°  = 29° الجوزاء
    8729 ÷ 12  = 727.4 ⇒ 7°   = 7° الحمل      (المشترى: 12 سنة)
    8729 ÷ 30  = 291   ⇒ 291° = 21° الجدى      (زحل: 30 سنة)
    87.29 ÷ 1  = 87.29 ⇒ 27°17′ الجوزاء

والخطوات هنا:

    ١) محاور كبيرة (انعكاس ≥ 40%) — وحدها تُسمّى قممًا وقيعانًا رئيسية.
    ٢) قاعٌ رئيسى يسبقه قمةٌ رئيسية، وليس داخله محورٌ فرعى أخفض ⇒ ليس قاعًا فرعيًّا.
    ٣) الرقم عند القاع — بلا علامة. وتُميَّز خاناته.
    ٤) يُقرأ على الدائرة بمعدل حركة كل كوكب (÷1 · ÷12 · ÷30).
    ٥) تُقاس النسبة: الدرجة مقابل موضع الكوكب الحقيقى فى ذلك اليوم.

التشغيل:
    python3 tools/circle_one_stock.py --csv /tmp/egx_clean.csv --ticker AMOC --bottom 2016-02-11
"""

import argparse
import collections
import csv
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import astro_conjunctions as A  # noqa: E402

SIGNS = ("الحمل", "الثور", "الجوزاء", "السرطان", "الأسد", "العذراء",
         "الميزان", "العقرب", "القوس", "الجدى", "الدلو", "الحوت")
BODIES = ("mercury", "venus", "mars", "jupiter", "saturn",
          "uranus", "neptune", "pluto")
AR = {"sun": "الشمس", "mercury": "عطارد", "venus": "الزهرة", "mars": "المريخ",
      "jupiter": "المشترى", "saturn": "زحل", "uranus": "أورانوس",
      "neptune": "نبتون", "pluto": "بلوتو"}

RATES = (("الشمس", 1.0), ("المشترى", 12.0), ("زحل", 30.0))
PERIOD = {"الشمس": 1.0, "المشترى": 11.862, "زحل": 29.457}


def load(path):
    by = collections.defaultdict(dict)
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                h, l, c = float(r["high"]), float(r["low"]), float(r["close"])
            except ValueError:
                continue
            if c > 0 and l > 0:
                by[r["ticker"]][r["date"]] = (h, l, c)
    return {t: dict(sorted(v.items())) for t, v in by.items()}


def zigzag(px, th):
    piv, direction = [], 1
    hi = lo = px[0]
    hi_i = lo_i = 0
    for i, p in enumerate(px):
        if direction >= 0:
            if p > hi:
                hi, hi_i = p, i
            elif p < hi * (1 - th):
                piv.append(("H", hi_i, hi))
                direction, lo, lo_i = -1, p, i
        if direction <= 0:
            if p < lo:
                lo, lo_i = p, i
            elif p > lo * (1 + th):
                piv.append(("L", lo_i, lo))
                direction, hi, hi_i = 1, p, i
    return piv


def digits_of(price):
    """الرقم بلا علامة · خاناته · والأُسّ الذى يردّه إلى السعر.

    0.97  ⇒ 97  · 2 خانتين · k0 = −2
    2.98  ⇒ 298 · 3 خانات  · k0 = −2
    0.40  ⇒ 4   · 1 خانة   · k0 = −1
    """
    price = round(float(price), 2)
    s = f"{price:.2f}".replace(".", "").lstrip("0").rstrip("0")
    n = int(s) if s else 0
    k = next((kk for kk in range(-6, 7) if abs(n * 10.0 ** kk - price) < 1e-6), None)
    return n, len(str(n)), k


def fmt(lon):
    lon %= 360.0
    s, d = int(lon // 30), lon % 30
    return f"{int(d)}°{round((d - int(d)) * 60):02d}′ {SIGNS[s]}"


def bodies_on(date):
    y, m, d = map(int, date.split("-"))
    jd = A.date_to_jd(y, m, d)
    T = (jd - 2451545.0) / 36525.0
    prec = (5029.0966 * T + 1.11113 * T * T) / 3600.0
    out = {"sun": A.sun_longitude(jd) * A.R2D % 360.0}
    for b in BODIES:
        out[b] = (A.longitude(b, jd, "geo") * A.R2D + prec) % 360.0
    return out


def sep(a, b):
    d = abs((a - b) % 360.0)
    return min(d, 360.0 - d)


#  ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--ticker", default="AMOC")
    ap.add_argument("--bottom", help="YYYY-MM-DD")
    ap.add_argument("--major", type=float, default=0.40)
    ap.add_argument("--minor", type=float, default=0.25)
    ap.add_argument("--factor", type=float, default=1.0,
                    help="عامل تحويل السلسلة المعدَّلة إلى السعر الخام (سوق)")
    ap.add_argument("--from", dest="dfrom", help="ابدأ من هذا التاريخ (للفصل عن المقطع المعدَّل)")
    ap.add_argument("--money", action="store_true",
                    help="الوحدة قرش: الرقم = السعر × 100")
    ns = ap.parse_args()

    data = load(ns.csv)
    if ns.ticker not in data:
        sys.exit(f"السهم {ns.ticker} ليس فى الأرشيف")
    src = {d: t for d, t in data[ns.ticker].items()
           if not ns.dfrom or d >= ns.dfrom}
    if not src:
        sys.exit("لا صفوف فى هذا النطاق")
    v = {d: tuple(x * ns.factor for x in t) for d, t in src.items()}
    if ns.factor != 1.0:
        print(f"\n⚠ السلسلة معدَّلة — ضُربت فى {ns.factor:g} لتقدير السعر الخام.")
    dates = list(v)
    high = [v[d][0] for d in dates]
    low = [v[d][1] for d in dates]
    close = [v[d][2] for d in dates]

    W = 88
    print("=" * W)
    print(f"سهم واحد: {ns.ticker}  ·  {len(dates)} جلسة  ·  {dates[0]} → {dates[-1]}")
    print("=" * W)

    major = zigzag(close, ns.major)
    minor = zigzag(close, ns.minor)

    print(f"\n١ — المحاور الكبيرة (انعكاس ≥ {100 * ns.major:.0f}%)")
    print(f"   {'#':<4}{'النوع':<7}{'التاريخ':<14}{'قمة/قاع':>10}{'إغلاق':>10}")
    for k, (kind, i, p) in enumerate(major):
        px = high[i] if kind == "H" else low[i]
        print(f"   {k:<4}{'قمة' if kind == 'H' else 'قاع':<7}{dates[i]:<14}"
              f"{px:>10.4f}{p:>10.4f}")

    if ns.bottom:
        bi = dates.index(ns.bottom) if ns.bottom in v else sys.exit("ليس جلسة")
        prev = [x for x in major if x[0] == "H" and x[1] < bi]
        if not prev:
            sys.exit("لا قمة رئيسية قبله")
        top = prev[-1]
    else:
        cands = []
        for k in range(1, len(major) - 1):
            kind, i, p = major[k]
            if kind != "L" or major[k - 1][0] != "H":
                continue
            win = close[max(0, i - 60):i + 61]
            if abs(p - min(win)) < 1e-9:
                cands.append((1 - p / major[k - 1][2], i))
        if not cands:
            sys.exit("لا قاع رئيسى")
        bi = max(cands)[1]
        top = [x for x in major if x[0] == "H" and x[1] < bi][-1]

    ti = top[1]
    lo_b, hi_t = low[bi], high[ti]
    print(f"\n٢ — القاع الرئيسى: **{dates[bi]}**  ·  أدنى سعر **{lo_b:.4f}**"
          f" (إغلاق {close[bi]:.4f})")
    print(f"   القمة الرئيسية قبله: **{dates[ti]}**  ·  أعلى سعر **{hi_t:.4f}**"
          f" (إغلاق {top[2]:.4f})")
    print(f"   الهبوط: {hi_t:.4f} → {lo_b:.4f} = **−{100 * (1 - lo_b / hi_t):.1f}%**"
          f" فى {bi - ti} جلسة")
    inner = [x for x in minor if x[0] == "L" and ti < x[1] < bi]
    if inner:
        worst = min(low[x[1]] for x in inner)
        print(f"   محاور فرعية بينهما: {len(inner)} · أدنى قيعانها الفرعية {worst:.4f}")
        print(f"   ⇒ قاعنا {lo_b:.4f} {'أدنى منها ⇒ رئيسى لا فرعى ✔' if lo_b <= worst else 'ليس أدنى ✘'}")
    else:
        print("   ولا محور فرعى بينهما ⇒ القاع واحدٌ غير مُجزَّأ ✔")

    #  ── الرقم ────────────────────────────────────────────────────────
    if ns.money:
        lo_b = round(lo_b * 100.0, 2)
        print("\n  (الوحدة: قرش — الرقم = السعر × 100)")
    N, nd, k0 = digits_of(lo_b)
    reads = [N * 10.0 ** (k0 + j) for j in range(5)]
    print("\n" + "=" * W)
    print("٣ — الرقم — ولا علامة")
    print("=" * W)
    print(f"""
   السعر عند القاع (أدنى سعر): {lo_b:.4f}
   والرقم بلا علامة          : **{N}**  —  **{nd}**
   وقراءاته على الدائرة      : {' = '.join(f'{r:g}' for r in reads)}

   فالقاعدة: الرقم نفسه لا يتغيّر، وموضعُ القراءة هو المتغيّر.
      خانة واحدة : 2 = 200 = 200000
      خانتان     : 20 = 2000 = 200000
      و{nd}        : {reads[0]:g} = {reads[2]:g} = {reads[4]:g}
""")

    #  ── الدائرة ──────────────────────────────────────────────────────
    print("=" * W)
    print("٤ — الرقم على الدائرة · بمعدل حركة كل كوكب")
    print("=" * W)
    print(f"\n   {'معدل الحركة':<13}{'÷':>5}{'القراءة':>12}{'الدرجة':>10}{'البرج':>22}")
    rows = []
    for name, rate in RATES:
        for r in reads:
            deg = (r / rate) % 360.0
            rows.append((name, rate, r, deg))
            print(f"   {name:<13}{rate:>5g}{r:>12.4g}{deg:>10.2f}{fmt(deg):>22}")

    #  ── النسبة ───────────────────────────────────────────────────────
    print("\n" + "=" * W)
    print("٥ — النسبة مع الكوكب: الدرجة مقابل موضعه الحقيقى فى يوم القاع")
    print("=" * W)
    pos = bodies_on(dates[bi])
    print(f"\n   مواضع الكواكب فى {dates[bi]}:")
    for b in ("sun",) + BODIES:
        print(f"      {AR[b]:<8}{pos[b]:>9.2f}°   {fmt(pos[b])}")

    best = []
    for name, rate, r, deg in rows:
        b = min(pos, key=lambda k: sep(deg, pos[k]))
        best.append((sep(deg, pos[b]), name, rate, r, deg, b))
    best.sort()
    print(f"\n   الأقرب:")
    for d, name, rate, r, deg, b in best[:4]:
        print(f"      {r:>10.4g} ÷ {rate:<3g} = {deg:>8.2f}° ({fmt(deg)})"
              f"  ↔  {AR[b]} {pos[b]:.2f}°  ⇒ **{d:.2f}°**")

    #  ── اختبار الوحدة: أىُّ قراءةٍ تجعل 1×1 يعمل؟ ───────────────────
    print("\n" + "=" * W)
    print("٥.٥ — الوحدة: أىُّ قراءةٍ تجعل المدى = الزمن؟")
    print("=" * W)
    legs = []
    for k in range(1, len(major)):
        a, b = major[k - 1], major[k]
        days = (d2 := __import__("datetime").date)  # placeholder
        y1, m1, dd1 = map(int, dates[a[1]].split("-"))
        y2, m2, dd2 = map(int, dates[b[1]].split("-"))
        n = (d2(y2, m2, dd2) - d2(y1, m1, dd1)).days
        if n <= 0:
            continue
        legs.append((dates[a[1]], dates[b[1]], abs(b[2] - a[2]), n))
    print(f"\n  {'من':<12}{'إلى':<12}{'أيام':>7}{'مدى':>10}"
          f"{'×1':>9}{'×10':>9}{'×100':>9}")
    for a, b, rng, n in legs:
        print(f"  {a:<12}{b:<12}{n:>7}{rng:>10.2f}"
              f"{rng / n:>9.3f}{rng * 10 / n:>9.3f}{rng * 100 / n:>9.3f}")
    print("\n  ⇒ الوحدة الصحيحة هى التى يكون فيها العمود ≈ 1.000.")

    #  ── الضابط ───────────────────────────────────────────────────────
    print("\n" + "=" * W)
    print("٦ — الصدفة: كم مطابقةً تُتوقّع بلا أى معنى؟")
    print("=" * W)
    n = len(pos)
    p1 = n * 6.0 / 360.0
    hit3 = sum(1 for d, *_ in best if d <= 3.0)
    hit1 = sum(1 for d, *_ in best if d <= 1.0)
    print(f"""
   الخيارات: {len(rows)} (5 قراءات × 3 معدلات) · الكواكب: {n}
   احتمال مطابقة واحدة داخل ±3°: {100 * p1:.1f}%
   ⇒ المتوقَّع بالصدفة: **{p1 * len(rows):.1f} مطابقة** من {len(rows)}
      والذى وجدناه: **{hit3}** داخل ±3° · **{hit1}** داخل ±1°
""")


if __name__ == "__main__":
    main()
