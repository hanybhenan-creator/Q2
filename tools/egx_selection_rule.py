#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
قاعدة الاختيار عند جان — مقيسة. §17.8 من docs/04-selection-engine.md

نصّه (New Stock Trend Detector, 1936):

    «تداول دائمًا فى الأسهم التى تتجاوز قممها السابقة وتصنع قممًا أعلى
     وقيعانًا أعلى، فهى الأفضل للشراء، واترك الميتة الساكنة.»

فالقاعدة صريحة وقابلة للاختبار: **قمم أعلى + قيعان أعلى** خلال نصف سنة، مقابل
نصف السنة السابق. والسؤال: هل السهم المؤهَّل يتفوق على غيره فى النصف التالى —
مقارنةً بأقرانه فى التاريخ نفسه (لا بمتوسط السوق، فجان نفسه رفض المتوسطات).

الطريقة: إعادة توازن كل 126 يوم تداول (نصف سنة)، ولكل تاريخ يُحسب فرق واحد:
وسيط العائد المستقبلى للمؤهَّل ناقص وسيط غير المؤهَّل. ثم يُختبر متوسط الفروق
عبر التواريخ. والعائدات متداخلة إن لم تُباعد التواريخ، فالتاريخ هو وحدة القياس.

التشغيل:
    python3 tools/egx_selection_rule.py --csv /tmp/egx_clean.csv
"""

import argparse
import collections
import csv

import numpy as np

H = 126  # نصف سنة تداول


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--since", default="2013-01-01")
    ap.add_argument("--start", default="2014-01-02")
    ap.add_argument("--min-rows", type=int, default=800)
    ns = ap.parse_args()

    data = load(ns.csv, ns.since, ns.min_rows)
    obs = []
    for t, v in data.items():
        ds = sorted(v)
        px = np.array([v[d] for d in ds])
        for i in range(2 * H, len(px) - H):
            if ds[i] < ns.start:
                continue
            hi1, lo1 = px[i - H + 1:i + 1].max(), px[i - H + 1:i + 1].min()
            hi0 = px[i - 2 * H + 1:i - H + 1].max()
            lo0 = px[i - 2 * H + 1:i - H + 1].min()
            obs.append((ds[i], 1 if (hi1 > hi0 and lo1 > lo0) else 0,
                        px[i + H] / px[i] - 1,
                        (hi1 - lo1) / lo1))
    print(f"أسهم: {len(data)} · مشاهدات: {len(obs):,}")

    rebal = sorted({o[0] for o in obs})[::H]
    by_day = collections.defaultdict(list)
    for d, q, f, rng in obs:
        if d in set(rebal):
            by_day[d].append((q, f, rng))
    print(f"تواريخ إعادة التوازن: {len(by_day)}")

    gaps = []
    for d, v in sorted(by_day.items()):
        m = np.median([f for _, f, _ in v])
        q = [f - m for qq, f, _ in v if qq == 1]
        nq = [f - m for qq, f, _ in v if qq == 0]
        if len(q) >= 10 and len(nq) >= 10:
            gaps.append((d, np.median(q) - np.median(nq), len(q), len(nq)))
    g = np.array([x[1] for x in gaps])
    t = g.mean() / (g.std(ddof=1) / np.sqrt(len(g)))
    print(f"\nالفروق عبر {len(g)} تاريخًا (عائد 6 أشهر، منزوع وسيط السوق):")
    print(f"  الوسط {100 * g.mean():+.2f} نقطة · الوسيط {100 * np.median(g):+.2f}"
          f" · موجب فى {100 * np.mean(g > 0):.0f}% · t = {t:+.2f}")
    print("\n  التفصيل:")
    for d, v, nq, nn in gaps:
        print(f"    {d}: {100 * v:+7.2f}   (مؤهَّل {nq:3} · غير مؤهَّل {nn:3})")

    # النطاق الضيق: قاعدة «اترك الساكنة» — تُقاس بالمدى النسبى لنصف السنة.
    narrow = [(f, r) for d, q, f, r in obs if d in set(rebal)]
    rng = np.array([r for _, r in narrow])
    fwd = np.array([f for f, _ in narrow])
    allf = np.array([f for d, q, f, r in obs if d in set(rebal)])
    print(f"\n  قاعدة «اترك الساكنة»: نسبة المشاهدات فى نطاق <15% = "
          f"{100 * np.mean(rng < 0.15):.1f}% — عيّنة صغيرة لا تكفى للحكم")


if __name__ == "__main__":
    main()
