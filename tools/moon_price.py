#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
القمر والسعر — هل يمثّل القمر السعر؟

القول الشائع: «القمر يمثّل السعر، والشمس تمثّل الزمن». وهذا ملف يقيسه،
لا يقوله ولا ينفيه.

ولا يوجد «قمر هليوسنتريك»: القمر تابع للأرض، فطوله مركزى أرضى بالضرورة.
والنموذج هنا عناصر كبلرية مبسّطة (Meeus، الحدود الأولى):

    L' = 218.3164 + 481267.8812 T      (الطول الوسطى)
    D  = 297.8502 + 445267.1114 T      (الاستطالة الوسطى)
    M  = 357.5291 +  35999.0503 T      (شذوذ الشمس)
    M' = 134.9634 + 477198.8675 T      (شذوذ القمر)
    F  =  93.2721 + 483202.0175 T      (حجة العرض)

    λ = L' + 6.289 sin M' + 1.274 sin(2D−M') + 0.658 sin2D + 0.214 sin2M'
          − 0.186 sinM − 0.114 sin2F + …

والتحقق: كسوف كلى للشمس 2026-08-12 ⇒ الاستطالة صفر. والحد الأدنى للنموذج
0.1°، وهو أقل من أى أورب مستعمل بثلاثين ضعفًا.

والاختبارات أربعة، وكلها بضابط:
    أ  الطور والعائد        (هل يختلف العائد باختلاف طور القمر؟)
    ب  الانعطافات والطور    (هل تتكدّس الانعطافات عند طور؟ — رايلى)
    ج  الطيف                (هل للقمر تردد فى السعر؟)
    د  طول القمر ودرجة السعر (هل «السعر على وجه القمر» عند الانعطاف؟)

التشغيل:
    python3 tools/moon_price.py --csv /tmp/egx_clean.csv
"""

import argparse
import collections
import csv
import math
import sys

import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import astro_conjunctions as A  # noqa: E402

SYNODIC = 29.530588853
SIDEREAL = 27.321661
ASPECTS = (0.0, 60.0, 90.0, 120.0, 180.0)


def jd_of(date_str, hours=0.0):
    y, m, d = (int(x) for x in date_str.split("-"))
    return A.date_to_jd(y, m, d, hours)


def moon_longitude(jd):
    """الطول الظاهرى للقمر (درجات، اعتدال التاريخ)."""
    T = (jd - 2451545.0) / 36525.0
    Lp = 218.3164477 + 481267.88123421 * T - 0.0015786 * T * T
    D = 297.8501921 + 445267.1114034 * T - 0.0018819 * T * T
    M = 357.5291092 + 35999.0502909 * T - 0.0001536 * T * T
    Mp = 134.9633964 + 477198.8675055 * T + 0.0087414 * T * T
    F = 93.2720950 + 483202.0175233 * T - 0.0036539 * T * T
    r = math.radians
    d = (Lp
         + 6.288774 * math.sin(r(Mp))
         + 1.274027 * math.sin(r(2 * D - Mp))
         + 0.658314 * math.sin(r(2 * D))
         + 0.213618 * math.sin(r(2 * Mp))
         - 0.185116 * math.sin(r(M))
         - 0.114332 * math.sin(r(2 * F))
         + 0.058793 * math.sin(r(2 * D - 2 * Mp))
         + 0.057066 * math.sin(r(2 * D - M - Mp))
         + 0.053322 * math.sin(r(2 * D + Mp))
         - 0.045758 * math.sin(r(2 * D - M)))
    return d % 360.0


def phase(date_str):
    """طور القمر 0..360 = الاستطالة عن الشمس (0 = محاق، 180 = بدر)."""
    jd = jd_of(date_str)
    return (moon_longitude(jd) - A.sun_longitude(jd)) % 360.0


def check_model():
    print("=" * 76)
    print("٠ — ضبط النموذج")
    print("=" * 76)
    for date, hours in (("2026-08-12", 17.77), ("2026-02-17", 12.0), ("2025-03-29", 10.9)):
        jd = jd_of(date, hours)
        e = (moon_longitude(jd) - A.sun_longitude(jd)) % 360.0
        e = min(e, 360 - e)
        print(f"  {date} {int(hours):02d}:{int(60*(hours%1)):02d} UT   استطالة {e:5.2f}°"
              f"   {'محاق (كسوف 2026-08-12)' if abs(e) < 2 else ''}")
    # طول الشهر الاقترانى المحسوب
    jd, hits, prev = jd_of("2025-01-01"), [], None
    while jd < jd_of("2026-06-01"):
        e = (moon_longitude(jd) - A.sun_longitude(jd)) % 360.0
        e = e - 360 if e > 180 else e
        if prev is not None and prev > 0 >= e:
            lo, hi = jd - 0.25, jd
            for _ in range(40):
                m = (lo + hi) / 2
                x = (moon_longitude(m) - A.sun_longitude(m)) % 360.0
                x = x - 360 if x > 180 else x
                lo, hi = (m, hi) if x > 0 else (lo, m)
            hits.append((lo + hi) / 2)
        prev = e
        jd += 0.25
    gaps = np.diff(hits)
    print(f"  الشهر الاقترانى المحسوب: {gaps.mean():.4f} يومًا  (المرجع {SYNODIC})"
          f"   خطأ {86400 * abs(gaps.mean() - SYNODIC):.0f} ثانية")
    return abs(gaps.mean() - SYNODIC) < 0.01


def load(path, min_rows):
    by = collections.defaultdict(dict)
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                c = float(r["close"])
            except ValueError:
                continue
            if c > 0:
                by[r["ticker"]][r["date"]] = c
    return {t: dict(sorted(v.items())) for t, v in by.items()
            if not t.upper().startswith("EGX") and len(v) >= min_rows}


def zigzag(px, th=0.20, skip=30):
    p = px[skip:]
    if len(p) < 10:
        return []
    out, trend = [], 0
    hi = lo = p[0]
    hii = loi = 0
    for i, x in enumerate(p):
        if trend >= 0:
            if x > hi:
                hi, hii = x, i
            elif x <= hi * (1 - th):
                if trend > 0 or not out:
                    out.append(hii + skip)
                trend, lo, loi = -1, x, i
        if trend <= 0:
            if x < lo:
                lo, loi = x, i
            elif x >= lo * (1 + th):
                if trend < 0:
                    out.append(loi + skip)
                trend, hi, hii = 1, x, i
    return out


def rayleigh(angles_deg):
    th = np.radians(np.asarray(angles_deg))
    n = len(th)
    if n < 20:
        return None
    R = abs(np.exp(1j * th).mean())
    return n, R, math.exp(-n * R * R)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv")
    ap.add_argument("--min-rows", type=int, default=300)
    ap.add_argument("--shuffles", type=int, default=400)
    ns = ap.parse_args()

    check_model()
    if not ns.csv:
        return

    data = load(ns.csv, ns.min_rows)
    dates = sorted({d for v in data.values() for d in v})
    ph = {d: phase(d) for d in dates}
    print(f"\nأسهم {len(data)} · أيام {len(dates)} · الطور محسوب لكل يوم")

    # ── أ: الطور والعائد
    print("\n" + "=" * 76)
    print("أ — هل يختلف العائد باختلاف طور القمر؟")
    print("=" * 76)
    idx = {d: i for i, d in enumerate(dates)}
    for hz in (1, 5, 21):
        by_date = collections.defaultdict(list)
        for t, v in data.items():
            ds = list(v)
            for i, d in enumerate(ds[:-hz]):
                by_date[d].append(v[ds[i + hz]] / v[d] - 1)
        rows = [(ph[d], float(np.mean(r))) for d, r in by_date.items() if len(r) >= 30]
        x = np.array([r[0] for r in rows])
        y = np.array([r[1] for r in rows])
        y = y - y.mean()
        rng = np.random.default_rng(4)

        def stat(yy):
            return abs((np.exp(1j * np.radians(x)) * yy).sum()) / np.abs(yy).sum()

        obs = stat(y)
        # الضابط: إدارة سلسلة العوائد مقابل الطور — فيبقى التماسك الزمنى كما هو
        null = np.array([stat(np.roll(y, int(rng.integers(1, len(y)))))
                         for _ in range(ns.shuffles)])
        p = float(np.mean(null >= obs))
        print(f"  أفق {hz:2d} يومًا: ارتباط دائرى {obs:.3f} · ضابط إدارة {null.mean():.3f}±{null.std():.3f}"
              f" · p = {p:.2f}")

    # ── ب: الانعطافات والطور
    print("\n" + "=" * 76)
    print("ب — هل تتكدّس الانعطافات عند طور معيّن؟")
    print("=" * 76)
    piv, piv_dates_idx = [], []
    for t, v in data.items():
        ds = list(v)
        px = np.array([v[d] for d in ds], float)
        for i in zigzag(px):
            piv.append(ph[ds[i]])
            piv_dates_idx.append(idx[ds[i]])
    n, R, _ = rayleigh(piv)
    print(f"  انعطافات {n:,} · R = {R:.4f} · والطبيعى لو استقلّت {1/math.sqrt(n):.4f}")
    print("  ولا يُقرأ هذا وحده: الانعطافات تتزامن فى السوق، فعدد المستقلّات أقل بكثير من n.")
    piv_idx = [idx_ for idx_ in piv_dates_idx]
    rng = np.random.default_rng(8)
    null = []
    for _ in range(ns.shuffles):
        k = int(rng.integers(1, len(dates)))       # إزاحة زمنية واحدة: تُبقى تزامن السوق
        shifted = [ph[dates[(i + k) % len(dates)]] for i in piv_idx]
        _, Rn, _ = rayleigh(shifted)
        null.append(Rn)
    null = np.array(null)
    p_rot = float(np.mean(null >= R))
    print(f"  والضابط (إزاحة زمنية واحدة): {null.mean():.4f}±{null.std():.4f} · p = {p_rot:.3f}")

    # ── ج: الطيف عند تردد القمر
    print("\n" + "=" * 76)
    print("ج — هل للقمر تردد فى السعر؟")
    print("=" * 76)
    print(f"\n{'الدورة':<12}{'أيام':>8}{'نسبة القدرة':>14}{'فوق 2':>9}{'فوق 3':>9}")
    for name, period in (("اقترانية", SYNODIC), ("نجمية", SIDEREAL)):
        ratios = []
        for t, v in data.items():
            ds = list(v)
            if len(ds) < 1500:
                continue
            px = np.log(np.array([v[d] for d in ds], float))
            r = np.diff(px)
            r = r - r.mean()
            n = len(r)
            f0 = 1.0 / period
            def power(f):
                k = np.arange(n)
                return abs(np.dot(r, np.exp(-2j * np.pi * f * k))) ** 2 / n
            band = [power(f0 * (1 + s * 0.15)) for s in np.linspace(-0.8, 0.8, 33)
                    if abs(s) > 0.08]
            ratios.append(power(f0) / np.median(band))
        ratios = np.array(ratios)
        print(f"{name:<12}{period:>8.2f}{np.median(ratios):>14.2f}"
              f"{100 * np.mean(ratios > 2):>8.1f}%{100 * np.mean(ratios > 3):>8.1f}%")

    # مسح: هل 27.32 قمة محلية أم جزء من منحدر؟
    print("\n  مسح الدور 20–40 يومًا (وسيط النسبة على الأسهم):")
    scan = []
    for period in [20, 22, 24, 25, 26, 26.5, 27.0, 27.32, 27.7, 28, 29, 29.53, 30, 32, 34, 36, 38, 40]:
        rr = []
        for t, v in data.items():
            ds = list(v)
            if len(ds) < 1500:
                continue
            r = np.diff(np.log(np.array([v[d] for d in ds], float)))
            r = r - r.mean()
            n = len(r)
            f0 = 1.0 / period
            k = np.arange(n)
            def power(f):
                return abs(np.dot(r, np.exp(-2j * np.pi * f * k))) ** 2 / n
            band = [power(f0 * (1 + s_ * 0.15)) for s_ in np.linspace(-0.8, 0.8, 33) if abs(s_) > 0.08]
            rr.append(power(f0) / np.median(band))
        scan.append((period, float(np.median(rr))))
    line = "    " + "  ".join(f"{p_}:{v_:.2f}" for p_, v_ in scan)
    print(line)

    # الضابط: ترددات عشوائية
    rng = np.random.default_rng(12)
    ratios = []
    for t, v in data.items():
        ds = list(v)
        if len(ds) < 1500:
            continue
        px = np.log(np.array([v[d] for d in ds], float))
        r = np.diff(px)
        r = r - r.mean()
        n = len(r)
        f0 = 1.0 / rng.uniform(20, 40)
        def power(f):
            k = np.arange(n)
            return abs(np.dot(r, np.exp(-2j * np.pi * f * k))) ** 2 / n
        band = [power(f0 * (1 + s * 0.15)) for s in np.linspace(-0.8, 0.8, 33) if abs(s) > 0.08]
        ratios.append(power(f0) / np.median(band))
    ratios = np.array(ratios)
    print(f"{'ضابط عشوائى':<12}{'—':>8}{np.median(ratios):>14.2f}"
          f"{100 * np.mean(ratios > 2):>8.1f}%{100 * np.mean(ratios > 3):>8.1f}%")

    # ── د: درجة السعر وطول القمر
    print("\n" + "=" * 76)
    print("د — «السعر على وجه القمر» عند الانعطاف")
    print("=" * 76)
    hits = tot = 0
    ctrl_hits = 0
    mo = {d: moon_longitude(jd_of(d)) for d in dates}
    rng = np.random.default_rng(6)
    for t, v in data.items():
        ds = list(v)
        px = np.array([v[d] for d in ds], float)
        pool = list(px)
        for i in zigzag(px):
            d = ds[i]
            th = px[i] % 360.0
            s = abs((th - mo[d] + 180) % 360 - 180)
            if min(abs(s - a) for a in ASPECTS) <= 3.0:
                hits += 1
            tot += 1
            th2 = float(rng.choice(pool)) % 360.0
            s2 = abs((th2 - mo[d] + 180) % 360 - 180)
            if min(abs(s2 - a) for a in ASPECTS) <= 3.0:
                ctrl_hits += 1
    print(f"  انعطافات {tot:,} · على وجه القمر (±3°) فى {100 * hits / tot:.1f}%"
          f" · والضابط (سعر عشوائى من السهم نفسه) {100 * ctrl_hits / tot:.1f}%")
    print("  (ولا حاجة إلى وحدة حرّة: طول القمر يجرى 13° فى اليوم، فكل يوم طور جديد.)")


if __name__ == "__main__":
    main()
