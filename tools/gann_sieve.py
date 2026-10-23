#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
المِصفاة — إعادة هندسة طريقة جان فى اختيار الأسهم، من كتابه وحده.

الكتاب: W.D. Gann — Master Stock Market Course (464 صفحة، 19 فصلًا).
والفصول تُقرأ هنا **آلةً واحدة**، لا نصائح متفرقة. وثلاثة نصوص فيها هى العمود:

  (١) ف9 «مدى التذبذب»: «خذ القاع والقمم لأى حركة مهمة، اطرح القاع من القمم
      تحصل على المدى، ثم اقسم المدى على 8 — فهذه مستويات المقاومة. ثم اقسمه
      على 3 للثلث والثلثين.»

  (٢) ف4 «تربيع المدى»: «إذا كانت قمة السهم 28، فمربع 28×28 يمثل تربيع السعر
      بالزمن؛ فحين يتحرك السهم 28 يومًا أو 28 أسبوعًا أو 28 شهرًا، يكون قد
      رَبَّع مداه السعرى 28.» أى أن **الزمن يُقاس بوحدات المدى نفسه**.

  (٣) ف6 «المستويات الطبيعية»: قواعد 100 و9 و12 وأقسام الدائرة — وفى آخرها:
      «ستجد أن كثيرًا من هذه النقاط يقابل بعضها» ⇒ **القوة من التقاء القواعد**.

فالمصفاة تعمل على **دائرة واحدة لكل سهم**: مدى الحملة يُردّ إلى 360°، فيصير
السعر والزمن قابلين للقياس بدرجة واحدة. وهذا هو «تربيع المدى» لا تفسير له.

المراحل:
  ١. البنية    — قمم وقيعان أعلى، ونشاط (ف1، ف8، ف12)
  ٢. المربع    — درجة السعر ودرجة الزمن على دائرة المدى (ف4، ف9)
  ٣. طاقة الرقم — التقاء السعر بمستويات 100/9/12 وأقسام الدائرة (ف6، ف13)
  ٤. طاقة الزمن — التقاء الزمن بأقسام الدائرة وأرقام المaster (ف6، ف7، ف13)
  ٥. الدورة     — أطوال 3/5/7/12/20/30 سنة التى ينسبها لأجرام (ف7، ف10A)

التشغيل:
    python3 tools/gann_sieve.py --csv /tmp/egx_clean.csv --date 2025-10-27
    python3 tools/gann_sieve.py --csv /tmp/egx_clean.csv --backtest
"""

import argparse
import collections
import csv
import math

import numpy as np

# ── أرقام الكتاب ───────────────────────────────────────────────────────────
# ف6: أقسام الدائرة المهمة
CIRCLE_DIV = (2, 3, 4, 5, 6, 8, 9, 12, 16, 24, 32)
# ف6: أرقام أساس 100 و9 و12
B100 = [100 * k / 16 for k in range(1, 16)] + [100 / 3, 200 / 3]
B9 = [9 * k for k in range(1, 13)] + [9 * k + 4.5 for k in range(12)]
B12 = [12 * k for k in range(1, 9)]
# ف13: المaster numbers ومربعاتها
MASTER = [3, 5, 7, 9, 12]
SQUARES = [m * m for m in MASTER] + [49, 81, 144, 196]
# ف7: أطوال الدورات المنسوبة للأجرام (بالأيام)
YEAR_DAYS = 365.25
CYCLES_D = {3: 3 * YEAR_DAYS, 5: 5 * YEAR_DAYS, 7: 7 * YEAR_DAYS,
            12: 12 * YEAR_DAYS, 20: 20 * YEAR_DAYS, 30: 30 * YEAR_DAYS}
# ف6: زوايا مهمة (أقسام 90 على 8، ثم 90 على 3)
ANGLES = [90 * k / 8 for k in range(1, 8)] + [30.0, 60.0] + [45.0, 120.0, 135.0, 180.0]


def phi(x):
    """درجة الرقم على دائرة الضرب — مشتقة من «العلامة العشرية لا تفرّق» (§14.9)."""
    return (360.0 * math.log10(abs(x))) % 360.0


def circ_dist(a, b):
    d = abs((a - b) % 360.0)
    return 360.0 - d if d > 180.0 else d


def level_hits(value, levels, tol):
    """عدد مستويات القاعدة التى يقع عليها الرقم (بعد تطبيع العلامة العشرية)."""
    p = phi(value)
    return sum(1 for L in levels if circ_dist(p, phi(L)) <= tol)


def number_energy(price, tol=1.5):
    """طاقة الرقم: التقاء قواعد 100 و9 و12 ومركزات الدائرة على السعر."""
    s = 0
    s += level_hits(price, B100, tol)
    s += level_hits(price, B9, tol)
    s += level_hits(price, B12, tol)
    p = phi(price)
    for d in CIRCLE_DIV:
        for k in range(1, d):
            s += circ_dist(p, phi(360 * k / d)) <= tol
    return s


def time_energy(days, tol=1.0):
    """طاقة الزمن: كم قسمًا من الدائرة/المربعات/الدورات يقع عليه عدد الأيام."""
    s = 0
    for d in CIRCLE_DIV:
        base = 360.0 / d
        n = round(days / base)
        if n >= 1 and abs(days - n * base) <= tol:
            s += 1
    for q in SQUARES:
        n = round(days / q)
        if n >= 1 and abs(days - n * q) <= tol:
            s += 1
    for k, c in CYCLES_D.items():
        n = round(days / (c / 8))
        if n >= 1 and abs(days - n * (c / 8)) <= tol * 3:
            s += 0.5
    return s


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
    return {t: v for t, v in by.items()
            if not t.upper().startswith("EGX") and len(v) >= min_rows}


def campaign(dates, px, i, look=252):
    """الحملة الحالية: قاعها وقعها خلال نافذة، وقمتها."""
    lo_i = max(0, i - look)
    w = px[lo_i:i + 1]
    j_lo = int(np.argmin(w)) + lo_i
    j_hi = int(np.argmax(w)) + lo_i
    L, H = float(px[j_lo]), float(px[j_hi])
    return j_lo, L, j_hi, H


def score_row(dates, px, i, mode="full"):
    """درجة المصفاة عند اليوم i — خمس مراحل، كل واحدة تُرجع مساهمتها."""
    if i < 260:
        return None
    j_lo, L, j_hi, H = campaign(dates, px, i)
    R = H - L
    if R <= 0:
        return None
    P = float(px[i])
    t = i - j_lo                      # أيام من القاع
    k = R / 360.0                     # سعر/درجة — تربيع المدى (ف4)
    if k <= 0:
        return None
    theta_p = (P - L) / k             # درجة السعر على دائرة المدى
    # تربيع المدى: المدى كله = 360° سعريًا، والدورة الزمنية = 360 يومًا (ف4).
    # فحين يتساوى θp و θt يكون السعر قد قطع من مداه بقدر ما قطع الزمن من دائرته
    # — وذلك هو خط 45° من القاع.
    theta_t = t % 360.0

    # ١) البنية: قمم وقيعان أعلى خلال نصف سنة
    h1, l1 = px[i - 125:i + 1].max(), px[i - 125:i + 1].min()
    h0, l0 = px[i - 250:i - 125].max(), px[i - 250:i - 125].min()
    s_struct = 1.0 if (h1 > h0 and l1 > l0) else 0.0
    # اتجاه: فوق القاع بمسافة معتبرة، وداخل النصف الأعلى من المدى
    s_pos = 1.0 if (P - L) / R >= 0.5 else 0.0

    # ٢) المربع: (أ) القرب من زاوية ثابتة، (ب) تساوى درجة السعر ودرجة الزمن
    dp = min(circ_dist(theta_p, a) for a in ANGLES)
    dpt = circ_dist(theta_p, theta_t)
    s_square = 0.6 * max(0.0, 1.0 - dp / 30.0) + 0.9 * max(0.0, 1.0 - dpt / 30.0)

    # ٣) طاقة الرقم على السعر المطلق
    s_num = min(number_energy(P) / 3.0, 2.0)

    # ٤) طاقة الزمن من القاع
    s_time = min(time_energy(t) / 3.0, 2.0)

    # ٥) الدورة: هل الزمن من قمة/قاع كبير يقترب من قسم دورة (بالأيام)
    s_cyc = 0.0
    for c in CYCLES_D.values():
        for div in (4, 8, 16):
            base = c / div
            n = round(t / base)
            if n >= 1 and abs(t - n * base) <= max(3, 0.01 * base):
                s_cyc += 0.5
    s_cyc = min(s_cyc, 1.0)

    if mode == "trend":          # البنية والموقع وحدهما
        w = dict(struct=1.5, pos=1.0, square=0.0, num=0.0, time=0.0, cyc=0.0)
    elif mode == "gann":         # المربع والرقم والزمن والدورة وحدها
        w = dict(struct=0.0, pos=0.0, square=2.0, num=1.5, time=2.0, cyc=1.0)
    else:
        w = dict(struct=1.5, pos=1.0, square=2.0, num=1.5, time=2.0, cyc=1.0)
    total = (w["struct"] * s_struct + w["pos"] * s_pos + w["square"] * s_square
             + w["num"] * s_num + w["time"] * s_time + w["cyc"] * s_cyc)
    return dict(total=total, P=P, L=L, H=H, R=R, t=t, theta_p=theta_p,
                theta_t=theta_t, dp=dp, s_struct=s_struct, s_pos=s_pos,
                s_square=s_square, s_num=s_num, s_time=s_time, s_cyc=s_cyc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--since", default="2013-06-01")
    ap.add_argument("--min-rows", type=int, default=800)
    ap.add_argument("--date", default=None)
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--backtest", action="store_true")
    ap.add_argument("--mode", default="full", choices=["full", "trend", "gann"])
    ns = ap.parse_args()

    data = load(ns.csv, ns.since, ns.min_rows)
    print(f"أسهم: {len(data)}")

    if ns.date:
        target = ns.date
        rows = []
        for t, v in data.items():
            ds = sorted(v)
            if ds[-1] < target:
                continue
            i = max(j for j, d in enumerate(ds) if d <= target)
            r = score_row(ds, np.array([v[d] for d in ds]), i)
            if r:
                r["ticker"] = t
                rows.append(r)
        rows.sort(key=lambda r: -r["total"])
        print(f"\nتاريخ المصفاة: {target} · أسهم مُقيَّمة: {len(rows)}")
        print("\n" + "=" * 96)
        print(f"{'#':>2} {'سهم':6} {'درجة':>5} {'سعر':>8} {'مدى':>7} {'يوم':>4} "
              f"{'θسعر':>6} {'θزمن':>6} {'زاوية':>6} {'بنية':>4} {'رقم':>4} {'زمن':>4}")
        print("=" * 96)
        for n, r in enumerate(rows[:ns.top], 1):
            print(f"{n:>2} {r['ticker']:6} {r['total']:5.2f} {r['P']:8.2f} "
                  f"{r['R']:7.2f} {r['t']:4d} {r['theta_p']:6.0f} "
                  f"{r['theta_t']:6.0f} {r['dp']:6.1f} {r['s_struct']:4.0f} "
                  f"{r['s_num']:4.1f} {r['s_time']:4.1f}")
        return

    if ns.backtest:
        # اختبار: تاريخ إعادة توازن موحّد كل 126 يوم تداول؛ ثم عائد 126 يومًا.
        H = 126
        cal = sorted({d for v in data.values() for d in v})
        cal = [d for d in cal if d >= "2014-01-02"]
        rebal = cal[::H]
        diffs = []
        for rd in rebal:
            rows = []
            for t, v in data.items():
                ds = sorted(v)
                if ds[0] > rd or ds[-1] <= rd:
                    continue
                i = max(j for j, d in enumerate(ds) if d <= rd)
                if i + H >= len(ds):
                    continue
                r = score_row(ds, np.array([v[d] for d in ds]), i, ns.mode)
                if not r:
                    continue
                r["fwd"] = v[ds[i + H]] / v[ds[i]] - 1
                r["ticker"] = t
                rows.append(r)
            if len(rows) < 30:
                continue
            rows.sort(key=lambda r: -r["total"])
            q = max(3, len(rows) // 10)
            m = np.median([r["fwd"] for r in rows])
            top = np.median([r["fwd"] for r in rows[:q]]) - m
            bot = np.median([r["fwd"] for r in rows[-q:]]) - m
            diffs.append((rd, top, bot, len(rows)))
        if not diffs:
            print("لا تواريخ كافية")
            return
        top = np.array([x[1] for x in diffs])
        bot = np.array([x[2] for x in diffs])
        print(f"\nاختبار المصفاة [{ns.mode}]: {len(diffs)} تاريخًا · عائد 6 أشهر منزوعًا منه الوسيط")
        print(f"  العُشر الأعلى: وسط {100 * top.mean():+.2f}%  "
              f"t = {top.mean() / (top.std(ddof=1) / math.sqrt(len(top))):+.2f}")
        print(f"  العُشر الأدنى: وسط {100 * bot.mean():+.2f}%  "
              f"t = {bot.mean() / (bot.std(ddof=1) / math.sqrt(len(bot))):+.2f}")
        print(f"  الفارق: {100 * (top.mean() - bot.mean()):+.2f}% "
              f"· موجب فى {100 * np.mean(top > bot):.0f}% من التواريخ")
        print("\n  التفصيل:")
        for d, a, b, n in diffs:
            print(f"    {d}: أعلى {100 * a:+6.2f}% · أدنى {100 * b:+6.2f}% · ({n} سهمًا)")

if __name__ == "__main__":
    main()
