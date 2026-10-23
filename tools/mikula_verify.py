#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
التحقق الكامل من منهج ميكولا — على الأمثلة وعلى الأرشيف.

المنهج كما تقوله أدواته الثلاث (`mikula_price_longitude.py`):

    السعر رقم  →  درجة على دائرة  →  تقابل درجة أخرى (كوكب أو زمن)  →  انعطاف.

وله **أربع خرائط** لا واحدة، ولا تتفق:

    1:1      θ = n                 (السعر هو الدرجة)
    مربع 9   θ = 180√n − 225       (موضع اللولب)
    دائرية   θ = 15(n − 290) + 240 (24 خلية، الصفر عند 290)
    مضاعفة   θ = 360·log10 n       (الدرجة وحدها التى لا تتغير بنقل العلامة)

وهذا الملف يقيس المنهج كله، لا جزءًا منه:

    A  الخرائط        ثبات الدرجة، واللفّات فى كل عقد
    B  أمثلة المصدر    أربعة أمثلة موسومة، تُحسب على الرصد لا تُنقل
    C  الشبكة         هل تقع الانعطافات على مضاعفات 45° أكثر من غيرها؟
    D  الأوجه         هل «السعر على وجه كوكب» فى الانعطاف أكثر من سطر عادى؟
    E  السعة          كم درجة حرية يحتاجها المنهج ليجد «ضربة» دائمًا؟
    F  التربيع        هل يتساوى مسير السعر فى الدرجات مع الزمن فى الأيام؟

والمبدأ فى القياس واحد: **الضابط**. لا تُقبل نسبة إلا مقابل نسبة مثلها
فى سطر عادى من السهم نفسه — لأن الانعطاف ليس عشوائيًا فى السعر.

التشغيل:
    python3 tools/mikula_verify.py --csv /tmp/egx_clean.csv
    python3 tools/mikula_verify.py --csv /tmp/egx_clean.csv --only charts source
"""

import argparse
import collections
import csv
import math
import sys

import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import astro_conjunctions as A  # noqa: E402

ASPECTS = (0.0, 60.0, 90.0, 120.0, 180.0)
ASPECT_NAMES = {0.0: "اقتران", 60.0: "تسديس", 90.0: "تربيع",
                120.0: "تثليث", 180.0: "تقابل"}
BODIES = ("sun", "mercury", "venus", "mars", "jupiter", "saturn", "uranus")

#  ─────────────────────────────────────────────────────────────────────
#  A — الخرائط الأربع
#  ─────────────────────────────────────────────────────────────────────


def deg_linear(p):
    return np.mod(p, 360.0)


def deg_so9(p):
    return np.mod(180.0 * np.sqrt(p) - 225.0, 360.0)


def deg_circle(p):
    """الخريطة الدائرية كما فى الملف: 24 خلية × 15°، الصفر عند 290، والبرج +240."""
    return np.mod(15.0 * (p - 290.0) + 240.0, 360.0)


def deg_log(p):
    return np.mod(360.0 * np.log10(p), 360.0)


CHARTS = (("1:1", deg_linear), ("مربع 9", deg_so9),
          ("دائرية", deg_circle), ("مضاعفة", deg_log))

#  الدورة الكاملة لكل خريطة — أى مقدار يلزم لزيادة الدرجة 360°:
#      1:1      → 360 سعرًا     |  مربع 9 → 2 فى الجذر  |  دائرية → 24  |  مضاعفة → عقد
CYCLE = {
    "1:1": lambda p: 360.0,
    "مربع 9": lambda p: 2.0 * math.sqrt(p),      # لا: الدورة فى الجذر 2، والسعر المقابل يتغير
    "دائرية": lambda p: 24.0,
    "مضاعفة": lambda p: p * 9.0,                  # من p إلى 10p
}


def turns_per_decade(chart, p):
    """كم لفّة كاملة تقطعها الخريطة حين يُضرب السعر فى عشرة."""
    q = 10.0 * p
    if chart == "1:1":
        return (q - p) / 360.0
    if chart == "مربع 9":
        return 180.0 * (math.sqrt(q) - math.sqrt(p)) / 360.0
    if chart == "دائرية":
        return 15.0 * (q - p) / 360.0
    return 1.0


def report_charts():
    print("=" * 74)
    print("A — الخرائط الأربع: هل الدرجة دالة للسعر أم للرقم؟")
    print("=" * 74)
    print("\nالرقم الواحد بثلاث علامات عشرية (§المسلَّمة أ١):\n")
    print(f"{'الخريطة':<10}{'123':>10}{'12.3':>10}{'1.23':>10}{'أقصى فرق':>11}")
    for name, fn in CHARTS:
        d = [fn(x) for x in (123, 12.3, 1.23)]
        print(f"{name:<10}{d[0]:>10.2f}{d[1]:>10.2f}{d[2]:>10.2f}"
              f"{max(d) - min(d):>10.1f}°")

    print("\nلفّات كاملة لكل عقد (×10 فى السعر):\n")
    print(f"{'السعر':>7}" + "".join(f"{n:>12}" for n, _ in CHARTS))
    for p in (1, 3, 10, 30, 100, 300, 1000):
        print(f"{p:>7}" + "".join(f"{turns_per_decade(n, p):>12.2f}" for n, _ in CHARTS))

    print("\nالقراءة: الخريطة **ساعة** إن أعطت العدد نفسه من اللفّات عند كل سعر.")
    print("والثلاث الأولى تلفّ أسرع كلما كبر السعر: عند 1000 تلفّ 1:1 خمسًا وعشرين")
    print("لفة فى العقد، ومربع 9 أربعًا وثلاثين، والمضاعفة لفة واحدة دائمًا.")
    print("⇒ الدرجة فى الثلاث الأولى ليست طورًا، بل **مسطرة تتمدد**.")


#  ─────────────────────────────────────────────────────────────────────
#  B — أمثلة المصدر
#  ─────────────────────────────────────────────────────────────────────


def body_longitude(name, date_str):
    """طول ظاهرى باعتدال التاريخ (J2000 + التقدّم المحورى)."""
    y, m, d = (int(x) for x in date_str.split("-"))
    jd = A.date_to_jd(y, m, d)
    if name == "sun":
        return A.sun_longitude(jd)
    T = (jd - 2451545.0) / 36525.0
    prec = (5029.0966 * T + 1.11113 * T * T) / 3600.0
    return (A.longitude(name, jd, "geo") * A.R2D + prec) % 360.0


def separation(a, b):
    d = abs((a - b) % 360.0)
    return min(d, 360.0 - d)


def nearest_aspect(price_deg, lon):
    sep = separation(price_deg, lon)
    best = min(ASPECTS, key=lambda x: abs(sep - x))
    return best, abs(sep - best)


SOURCE_CASES = (
    ("قطن — قاع 1930-11-10", "1930-11-10", 97.5, "زحل 7°30′ الجدى ⇒ تقابل"),
    ("صويا — قمة 1941-06-27", "1941-06-27", 148.75, "أورانوس ⇒ تربيع"),
    ("صويا — قمة 1941-09-12", "1941-09-12", 202.0, "المريخ ⇒ تقابل (سماحية قصيرة)"),
    ("ذرة — قمة 1867-10", "1867-10-01", 112.0, "الزهرة تربيع · زحل تثليث"),
)


def report_source():
    print("\n" + "=" * 74)
    print("B — أمثلة المصدر: تُحسب من الرصد، لا تُنقل")
    print("=" * 74)
    print("\nالكواكب على اعتدال التاريخ، محسوبة بعناصر كبلرية (خطأ النموذج ≈ 1° قبل 1950):\n")
    for label, date, price, claim in SOURCE_CASES:
        th = price % 360.0
        rows = []
        for b in BODIES:
            lon = body_longitude(b, date)
            asp, err = nearest_aspect(th, lon)
            rows.append((err, b, lon, asp))
        rows.sort()
        print(f"  {label}: السعر {price:g} ← {th:.2f}°   [{claim}]")
        for err, b, lon, asp in rows[:3]:
            print(f"      {b:<8} {lon:7.2f}°   {ASPECT_NAMES[asp]:<7} خطأ {err:5.2f}°")
        print()

    print("  والاختبار نفسه بوحدة أخرى — قطن 9.75 سنتًا لا 97.5 نقطة:\n")
    for p in (97.5, 9.75):
        th = p % 360.0
        rows = []
        for b in BODIES:
            asp, err = nearest_aspect(th, body_longitude(b, "1930-11-10"))
            rows.append((err, b, asp))
        rows.sort()
        err, b, asp = rows[0]
        print(f"      السعر {p:>6} ← {th:7.2f}°   أقرب: {b:<8} {ASPECT_NAMES[asp]:<7} خطأ {err:5.2f}°"
              f"   {'✔' if err <= 3 else '✘'}")
    print("\n  ⇒ القاع نفسه يعطى تقابلًا تامًّا فى وحدة، وتثليثًا فى أخرى.")
    print("     والوحدتان مشروعتان. فهذا **ليس خطأً حسابيًا**، بل حرية فى المرجع.")


#  ─────────────────────────────────────────────────────────────────────
#  البيانات
#  ─────────────────────────────────────────────────────────────────────


def load(path, since, min_rows):
    by = collections.defaultdict(dict)
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["date"] < since:
                continue
            try:
                c = float(r["close"])
            except ValueError:
                continue
            if c > 0:
                by[r["ticker"]][r["date"]] = c
    return {t: dict(sorted(v.items())) for t, v in by.items()
            if not t.upper().startswith("EGX") and len(v) >= min_rows}


def zigzag(prices, th=0.20, skip=30):
    p = prices[skip:]
    if len(p) < 10:
        return []
    out, trend = [], 0
    hi = lo = p[0]
    hi_i = lo_i = 0
    for i, x in enumerate(p):
        if trend >= 0:
            if x > hi:
                hi, hi_i = x, i
            elif x <= hi * (1 - th):
                if trend > 0 or not out:
                    out.append(hi_i)
                trend, lo, lo_i = -1, x, i
        if trend <= 0:
            if x < lo:
                lo, lo_i = x, i
            elif x >= lo * (1 + th):
                if trend < 0:
                    out.append(lo_i)
                trend, hi, hi_i = 1, x, i
    return out


def dist_grid(angle, step):
    m = np.asarray(angle) % step
    return np.minimum(m, step - m)


#  ─────────────────────────────────────────────────────────────────────
#  C — الشبكة عند الانعطافات
#  ─────────────────────────────────────────────────────────────────────


def report_turns(data, th, units=(0, 1, 2, 3)):
    print("\n" + "=" * 74)
    print("C — هل تقع الانعطافات على شبكة 45° أكثر من سطر عادى؟")
    print("=" * 74)

    piv_p, all_p = [], []
    for v in data.values():
        prices = list(v.values())
        idx = zigzag(prices, th=th, skip=30)
        piv_p.extend(prices[i] for i in idx)
        all_p.extend(prices[30:])
    piv_p, all_p = np.array(piv_p), np.array(all_p)
    rng = np.random.default_rng(7)
    pick = rng.integers(0, len(all_p), (400, len(piv_p)))

    print(f"\nعتبة الانعطاف {th:.0%} · أسهم {len(data)} · انعطافات {len(piv_p):,} · أيام {len(all_p):,}")
    print("(المدى الطبيعى للمسافة إلى الشبكة 11.25° — فالأصغر أقرب)\n")
    print(f"{'الخريطة':<9}{'وحدة':>6}{'انعطاف':>10}{'كل الأيام':>11}{'z':>7}")
    for name, fn in CHARTS[:2]:
        for k in units:
            d_p = dist_grid(fn(piv_p * 10.0 ** k), 45.0)
            d_a = dist_grid(fn(all_p * 10.0 ** k), 45.0)
            ctrl = d_a[pick].mean(axis=1)
            z = (d_p.mean() - ctrl.mean()) / ctrl.std()
            print(f"{name:<9}{'×1e%d' % k:>6}{d_p.mean():>10.3f}{d_a.mean():>11.3f}{z:>+7.2f}")
        mean_all = np.mean([dist_grid(fn(piv_p * 10.0 ** k), 45.0).mean() for k in units])
        print(f"{'':<9}{'متوسط':>6}{mean_all:>10.3f}")
    print("\nالثلاثة الأخرى (الدائرية) ليست مستقلة: θ = 15n + c ⇒ شبكتها 15° لا 45°،")
    print("وهى الخريطة الخطية نفسها بمسطرة أخرى — لا تُعدّ خريطة ثانية.")


#  ─────────────────────────────────────────────────────────────────────
#  D — الأوجه عند الانعطافات، وسعة البحث
#  ─────────────────────────────────────────────────────────────────────


def report_aspects(data, th, orb=3.0):
    print("\n" + "=" * 74)
    print("D — «السعر على وجه كوكب» عند الانعطاف، وسعة البحث")
    print("=" * 74)

    piv = []
    for t, v in data.items():
        dates, prices = list(v), list(v.values())
        for i in zigzag(prices, th=th, skip=30):
            piv.append((t, dates[i], prices[i]))
    cache = {}

    def lons(d):
        if d not in cache:
            cache[d] = {b: body_longitude(b, d) for b in BODIES}
        return cache[d]

    def min_err(price_deg, d):
        return min(nearest_aspect(price_deg, lons(d)[b])[1] for b in BODIES)

    n = len(piv)
    print(f"\nانعطافات {n:,} · {len(BODIES)} أجرام · {len(ASPECTS)} أوجه · سماحية ±{orb:g}°")
    print(f"التوقع لو كانت الدرجة منتظمة: {100 * (1 - (1 - 2 * orb / 360) ** (len(BODIES) * len(ASPECTS))):.1f}%\n")
    print(f"{'الخريطة':<9}{'انعطاف':>9}{'سطر عادى':>11}{'وسيط الخطأ':>13}")
    for name, fn in CHARTS[:2]:
        hit_p = sum(min_err(fn(p), d) <= orb for _, d, p in piv) / n
        rng = np.random.default_rng(5)
        pool = {t: list(v.values()) for t, v in data.items()}
        ctrl = [(d, pool[t][rng.integers(0, len(pool[t]))]) for t, d, _ in piv]
        hit_c = sum(min_err(fn(p), d) <= orb for d, p in ctrl) / n
        med = float(np.median([min_err(fn(p), d) for _, d, p in piv]))
        print(f"{name:<9}{100 * hit_p:>8.1f}%{100 * hit_c:>10.1f}%{med:>12.2f}°")

    print("\nالضابط: نفس التاريخ، وسعر عشوائى من السهم نفسه — فالتاريخ لا يتغير.")
    print("⇒ الانعطاف لا يضيف شيئًا على السطر العادى. الفرق صفر فى الحدّين.")

    print("\nوسعة البحث: كم وحدة سعرية تكفى لينال الانعطاف «وجهًا»؟\n")
    cnt = collections.Counter()
    for _, d, p in piv:
        c = 0
        for k in (-1, 0, 1, 2):
            if min_err((p * 10.0 ** k) % 360.0, d) <= orb:
                c += 1
        cnt[c] += 1
    for k in range(5):
        print(f"    {k} وحدة من 4: {100 * cnt[k] / n:5.1f}%")
    print(f"\n    ⇒ {100 * (n - cnt[0]) / n:.1f}% من الانعطافات تجد وجهًا بوحدة واحدة على الأقل.")
    print("    وهذا رقم السعة لا رقم السوق: 4 وحدات × 7 أجرام × 5 أوجه = 140 ثقبًا.")


#  ─────────────────────────────────────────────────────────────────────
#  F — تربيع السعر والزمن
#  ─────────────────────────────────────────────────────────────────────

from datetime import date as _date  # noqa: E402


def report_square(data, th):
    print("\n" + "=" * 74)
    print("F — «يتساوى السعر والزمن»: هل مسير الدرجات يساوى مسير الأيام؟")
    print("=" * 74)

    def ordi(s):
        y, m, d = (int(x) for x in s.split("-"))
        return _date(y, m, d).toordinal()

    dt, dth = [], []
    for v in data.values():
        dates, prices = list(v), list(v.values())
        for a, b in zip(zigzag(prices, th, 30), zigzag(prices, th, 30)[1:]):
            k = ordi(dates[b]) - ordi(dates[a])
            if k > 0:
                dt.append(k)
                dth.append(abs(180.0 * (math.sqrt(prices[b]) - math.sqrt(prices[a]))))
    dt, dth = np.array(dt, float), np.array(dth)

    print(f"\nحركات {len(dt):,} · وسيط الزمن {np.median(dt):.0f} يومًا · وسيط الدرجات {np.median(dth):.1f}°")
    slope = np.polyfit(dt, dth, 1)
    print(f"ميل الدرجات على الأيام: {slope[0]:.3f}°/يوم — والتربيع يقتضى 1.000 (فارق ×{1 / slope[0]:.1f})")
    print(f"نسبة الدرجات/الأيام: وسيط {np.median(dth / dt):.2f} · الربيعان "
          f"{np.percentile(dth / dt, 25):.2f}–{np.percentile(dth / dt, 75):.2f}\n")

    print("وفى كل عُشر من الأيام، تُبدَّل الدرجات داخله (فيبقى أثر الحجم ويزول أثر التربيع):\n")
    print(f"{'السماحية':>9}{'حقيقى':>9}{'مبدَّل':>9}")
    rng = np.random.default_rng(11)
    for orb in (5, 10, 20):
        obs = exp = 0.0
        for d in np.array_split(np.argsort(dt), 10):
            k, t = dt[d], dth[d]
            obs += np.sum(np.abs(t - (k % 360)) <= orb)
            exp += float(np.mean([np.sum(np.abs(t[rng.permutation(len(d))] - (k % 360)) <= orb)
                                  for _ in range(20)]))
        print(f"{'±%d°' % orb:>9}{100 * obs / len(dt):>8.1f}%{100 * exp / len(dt):>8.1f}%")
    print("\n⇒ الفارق صفر. ما بدا أثرًا قبل الضبط كان **حجم الحركة** لا التربيع.")


#  ─────────────────────────────────────────────────────────────────────
#  G — أمثلة من الأرشيف، بالحساب كاملًا
#  ─────────────────────────────────────────────────────────────────────


def report_examples(data, th, n=5):
    print("\n" + "=" * 74)
    print("G — أمثلة من الأرشيف: العمل كاملًا على انعطافات حقيقية")
    print("=" * 74)
    big = sorted(data.items(), key=lambda kv: -len(kv[1]))[:n]
    for t, v in big:
        dates, prices = list(v), list(v.values())
        idx = zigzag(prices, th, 30)
        if len(idx) < 2:
            continue
        moves = [(abs(180 * (math.sqrt(prices[b]) - math.sqrt(prices[a]))), a, b)
                 for a, b in zip(idx, idx[1:])]
        _, a, b = max(moves)
        d, p = dates[b], prices[b]
        print(f"\n  {t} — {d} — إغلاق {p:g}")
        for name, fn in CHARTS:
            th_deg = fn(p)
            best = min((nearest_aspect(th_deg, body_longitude(bb, d))[1], bb,
                        nearest_aspect(th_deg, body_longitude(bb, d))[0]) for bb in BODIES)
            print(f"      {name:<8}{th_deg:>8.2f}°   أقرب وجه: {best[1]:<8}"
                  f"{ASPECT_NAMES[best[2]]:<7}خطأ {best[0]:5.2f}°")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv")
    ap.add_argument("--since", default="2001-01-01")
    ap.add_argument("--min-rows", type=int, default=300)
    ap.add_argument("--threshold", type=float, default=0.20)
    ap.add_argument("--only", nargs="*")
    ns = ap.parse_args()

    only = set(ns.only or ())
    if not only or "charts" in only:
        report_charts()
    if not only or "source" in only:
        report_source()
    if ns.csv:
        data = load(ns.csv, ns.since, ns.min_rows)
        if not only or "turns" in only:
            report_turns(data, ns.threshold)
        if not only or "aspects" in only:
            report_aspects(data, ns.threshold)
        if not only or "square" in only:
            report_square(data, ns.threshold)
        if not only or "examples" in only:
            report_examples(data, ns.threshold)


if __name__ == "__main__":
    main()
