#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
الاختبار الفلكى — هل تقع انعطافات أسهم EGX عند زوايا الكواكب؟

هذا هو الاختبار الذى يقتضيه إطار جان نفسه، لا إطار التحليل المالى. وفيه
**لا يُستخدم عائد ولا ارتباط** — الوحيد المستخدم هو **الزمن**: تاريخ
الانعطاف مقابل تاريخ الزاوية.

السبب أن الزمن وحده هو ما ينجو من برهان §14.1: مضاعفة السعر تُزيح الدرجة
بثابت، فلا معنى لمقارنة «درجة السعر» بطول كوكب. أما **وقوع الحدث فى تاريخ**
فلا يتأثر بأى مضاعفة. فاختبار الزمن هو الاختبار المشروع، واختبار الدرجة
المطلقة غير قابل للتكذيب على هذه البيانات.

ثلاثة أسئلة:

  ١) **الزاوية:** هل يقترب انعطاف السهم من زاوية دقيقة بين كوكبين (0 · 30 ·
     45 · 60 · 90 · 120 · 135 · 150 · 180) أكثر من الصدفة؟ الضابط: إدارة
     تواريخ كل سهم على أيامه هو (تحفظ بنية السهم وتكسر المحاذاة).

  ٢) **السرعة:** يقول جان إن الأسهم تُقسَّم إلى كواكب سريعة/متوسطة/بطيئة.
     فهل الأزواج التى تقع فى صنف سرعة واحد أشد تزامنًا من الأزواج بين
     الأصناف؟ الضابط: خلط بطاقات التصنيف بين الأسهم.

  ٣) **الدورة:** هل تقع أطول موجة فى كل سهم عند طول كوكبى (88 · 225 · 687
     يومًا) أكثر من التوزيع المنتظم؟

التشغيل:
    python3 tools/egx_astro_test.py --csv /tmp/egx_clean.csv --trials 300
"""

import argparse
import collections
import csv
import itertools
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from astro_conjunctions import BODIES, body_longitude, date_to_jd  # noqa: E402

ASPECTS = (0.0, 30.0, 45.0, 60.0, 90.0, 120.0, 135.0, 150.0, 180.0)
# أطوال مدارية وسينودية (يوم) — تُختبر ضدها أطوال الموجات.
PLANET_PERIODS = {"عطارد 88": 87.97, "عطارد سينودى 116": 115.88,
                  "الزهرة 225": 224.70, "الزهرة سينودى 584": 583.92,
                  "المريخ 687": 686.98, "المريخ سينودى 780": 779.94}


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


def angular_sep(a, b):
    d = abs((a - b) % 360.0)
    return 360.0 - d if d > 180.0 else d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--since", default="2014-01-01")
    ap.add_argument("--min-rows", type=int, default=1000)
    ap.add_argument("--trials", type=int, default=300)
    ap.add_argument("--threshold", type=float, default=0.20)
    ns = ap.parse_args()

    data = load(ns.csv, ns.since, ns.min_rows)
    days = sorted({d for v in data.values() for d in v})
    idx = {d: i for i, d in enumerate(days)}
    print(f"أسهم: {len(data)} · أيام تداول: {len(days):,} · "
          f"{days[0]} → {days[-1]}")

    # ── الانعطافات
    pivots = {}
    speeds = {}
    for t, v in data.items():
        ds = sorted(v)
        pv = zigzag([v[d] for d in ds], ns.threshold)
        pos = [i + 30 for i in pv]
        pivots[t] = pos
        if len(pos) >= 3:
            lens = [b - a for a, b in zip(pos, pos[1:]) if 20 <= b - a <= 1500]
            if lens:
                speeds[t] = float(np.median(lens))
    n_piv = sum(len(p) for p in pivots.values())
    print(f"انعطافات: {n_piv:,} · أسهم لها سرعة: {len(speeds)}")

    # ── أطوال الأجرام على أيام التداول
    print("\nحساب أطوال الأجرام…")
    jd = [date_to_jd(int(d[:4]), int(d[5:7]), int(d[8:10])) for d in days]
    lon = {b: np.array([body_longitude(b, j) for j in jd]) for b in BODIES}

    pairs = list(itertools.combinations(BODIES, 2))
    dist = np.empty((len(days), len(pairs)))
    for k, (a, b) in enumerate(pairs):
        sep = np.abs((lon[a] - lon[b] + 180.0) % 360.0 - 180.0)  # 0..180
        d = np.full(len(days), 90.0)
        for asp in ASPECTS:
            d = np.minimum(d, np.abs(sep - asp))
        dist[:, k] = d
    print(f"أزواج الكواكب: {len(pairs)} · وسط أقرب زاوية: "
          f"{np.median(dist):.1f}°")

    # ── ١) هل الانعطافات أقرب إلى الزوايا؟
    print("\n" + "=" * 72)
    print("  ١) الزاوية — أقرب زاوية دقيقة عند الانعطاف مقابل إدارة عشوائية")
    print("=" * 72)
    rng = np.random.default_rng(4)
    seqs = {t: np.array([idx[d] for d in sorted(data[t])]) for t in pivots}
    piv_pos = {t: np.array(p) for t, p in pivots.items() if p}

    obs = np.zeros(len(pairs))
    for t, pos in piv_pos.items():
        s = seqs[t]
        obs += dist[s[pos]].sum(axis=0)
    obs /= n_piv

    null = np.empty((ns.trials, len(pairs)))
    for k in range(ns.trials):
        acc = np.zeros(len(pairs))
        for t, pos in piv_pos.items():
            s = seqs[t]
            off = int(rng.integers(0, len(s)))
            acc += dist[s[(pos + off) % len(s)]].sum(axis=0)
        null[k] = acc / n_piv

    pvals = (null <= obs).mean(axis=0)
    print(f"  متوسط المسافة عند الانعطاف: {obs.mean():.2f}° · "
          f"العدم {null.mean():.2f}° ± {null.mean(axis=0).std():.2f}")
    print("\n  أقل خمسة أزواج مسافةً (أى أشد محاذاة):")
    order = np.argsort(obs)[:5]
    for i in order:
        print(f"    {pairs[i][0]:8}↔{pairs[i][1]:8}  {obs[i]:5.2f}°  "
              f"(العدم {null[:, i].mean():5.2f}°)  p = {pvals[i]:.3f}")
    print(f"\n  أزواج عند p<0.05: {(pvals < 0.05).sum()} من {len(pairs)} "
          f"(المتوقع بالصدفة {0.05 * len(pairs):.2f})")
    print(f"  أقل p بعد تصحيح بونفيرونى: {pvals.min() * len(pairs):.3f}")

    # الحجم لا الدلالة: نسبة الانعطافات داخل درجة واحدة — ولها ضابطها.
    obs_near = np.mean([(dist[seqs[t][pos]] < 1.0).mean()
                        for t, pos in piv_pos.items()])
    rng2 = np.random.default_rng(8)
    nul_near = []
    for _ in range(ns.trials):
        acc = []
        for t, pos in piv_pos.items():
            s_ = seqs[t]
            off = int(rng2.integers(0, len(s_)))
            acc.append((dist[s_[(pos + off) % len(s_)]] < 1.0).mean())
        nul_near.append(np.mean(acc))
    nul_near = np.array(nul_near)
    print(f"\n  انعطافات داخل 1° من زاوية: {100 * obs_near:.1f}% · "
          f"العدم {100 * nul_near.mean():.1f}% ± {100 * nul_near.std():.1f}"
          f" · p = {(nul_near >= obs_near).mean():.3f}")
    print(f"  وحجم الأثر: {obs.mean():.2f}° مقابل {null.mean():.2f}° — "
          f"فرق {100 * (null.mean() - obs.mean()) / null.mean():.1f}% من المسافة")

    # هل الإشارة محمولة بأيام قليلة؟
    cnt = collections.Counter()
    for t, pos in piv_pos.items():
        for p in seqs[t][pos]:
            cnt[int(p)] += 1
    top_days = [d for d, _ in cnt.most_common(5)]
    keep = np.ones(n_piv, bool)
    k = 0
    for t, pos in piv_pos.items():
        for p in seqs[t][pos]:
            if int(p) in top_days:
                keep[k] = False
            k += 1
    acc = np.zeros(len(pairs))
    k = 0
    for t, pos in piv_pos.items():
        for p in seqs[t][pos]:
            if keep[k]:
                acc += dist[p]
            k += 1
    trimmed = acc / keep.sum()
    print(f"  بعد حذف أكثر 5 أيام ازدحامًا: متوسط المسافة {trimmed.mean():.2f}° "
          f"(كان {obs.mean():.2f}°)")

    # الموسمية: توزيع الانعطافات على الشهور — تفسير بديل لمحاذاة الشمس.
    months = collections.Counter()
    for t, pos in piv_pos.items():
        for p in seqs[t][pos]:
            months[int(days[int(p)][5:7])] += 1
    tot = sum(months.values())
    print("\n  توزيع الانعطافات على الشهور (يُفسّر أى محاذاة مع الشمس):")
    print("    " + " · ".join(f"{m:02d}:{100 * months[m] / tot:.0f}%"
                              for m in range(1, 13)))

    # ── ٢) الأصناف: سريع/متوسط/بطىء
    print("\n" + "=" * 72)
    print("  ٢) السرعة — هل الصنف الواحد يتزامن أكثر من بين الأصناف؟")
    print("=" * 72)
    ids = [t for t in speeds if len(pivots[t]) >= 6]
    srt = sorted(ids, key=lambda t: speeds[t])
    q = len(srt) // 4
    cls = {}
    for i, t in enumerate(srt):
        cls[t] = min(i // max(q, 1), 3)
    names = ["سريع", "متوسط", "بطىء", "بطىء جدًا"]
    for c in range(4):
        m = [t for t in srt if cls[t] == c]
        print(f"    {names[c]:10} {len(m):3} سهمًا · وسيط الطور "
              f"{np.median([speeds[t] for t in m]):.0f} يومًا")
    sp = np.array([speeds[t] for t in srt])
    print(f"    المدى {sp.min():.0f}–{sp.max():.0f} يومًا · "
          f"معامل الاختلاف {sp.std() / sp.mean():.2f} — تدرّج لا أربع كتل")
    edges = np.percentile(sp, [10, 25, 50, 75, 90]).round(0).astype(int)
    print(f"    العشريات/الربعيات: {' · '.join(map(str, edges))}")

    P = {t: set(pivots[t]) for t in ids}
    span = len({p for t in ids for p in P[t]}) or 1
    lift = {}
    for a, b in itertools.combinations(ids, 2):
        e = len(P[a]) * len(P[b]) / span
        if e > 0:
            lift[(a, b)] = len(P[a] & P[b]) / e
    within = [v for (a, b), v in lift.items() if cls[a] == cls[b]]
    between = [v for (a, b), v in lift.items() if cls[a] != cls[b]]
    print(f"\n    رفع داخل الصنف: {np.mean(within):.2f}× (n={len(within)}) · "
          f"بين الأصناف: {np.mean(between):.2f}× (n={len(between)})")

    labels = np.array([cls[t] for t in ids])
    obs_gap = np.mean(within) - np.mean(between)
    gaps = []
    for _ in range(ns.trials):
        sh = rng.permutation(labels)
        c2 = {t: int(sh[i]) for i, t in enumerate(ids)}
        w = [v for (a, b), v in lift.items() if c2[a] == c2[b]]
        bw = [v for (a, b), v in lift.items() if c2[a] != c2[b]]
        gaps.append(np.mean(w) - np.mean(bw))
    gaps = np.array(gaps)
    print(f"    الفرق {obs_gap:+.3f} · العدم {gaps.mean():+.3f} ± {gaps.std():.3f}"
          f" · p = {(gaps >= obs_gap).mean():.3f}")

    # ── ٣) الطول: هل تتجمع الموجات عند أطوال الكواكب؟
    print("\n" + "=" * 72)
    print("  ٣) الدورة — أطول موجة فى كل سهم مقابل أطوال الكواكب")
    print("=" * 72)
    peaks = []
    for t, v in data.items():
        ds = sorted(v)
        x = np.log(np.array([v[d] for d in ds]))
        if len(x) < 400:
            continue
        x = x - x.mean()
        n = len(x)
        f = np.abs(np.fft.rfft(x * np.hanning(n))) ** 2
        fr = np.fft.rfftfreq(n)
        ok = (fr > 1 / 750.0) & (fr < 1 / 30.0)
        if not ok.any():
            continue
        peaks.append(1.0 / fr[ok][np.argmax(f[ok])])
    peaks = np.array(peaks)
    print(f"  الأسهم: {len(peaks)} · وسيط الطول {np.median(peaks):.0f} يومًا · "
          f"الربعيات {np.percentile(peaks, 25):.0f}/{np.percentile(peaks, 75):.0f}")

    # الضابط الصحيح: مسار عشوائى بنفس التقلب — فسلسلة السعر ليست بيضاء،
    # وذروتها تقع بطبيعتها عند أطول طول متاح. بلا هذا الضابط يصير
    # «التجمع عند 687» مجرد أثر الاتجاه.
    rng3 = np.random.default_rng(21)
    sur = []
    for t, v in data.items():
        ds = sorted(v)
        x = np.log(np.array([v[d] for d in ds]))
        if len(x) < 400:
            continue
        r = np.diff(x)
        walk = np.concatenate([[0.0], np.cumsum(rng3.normal(0, r.std(), len(r)))])
        n = len(walk)
        f = np.abs(np.fft.rfft(walk * np.hanning(n))) ** 2
        fr = np.fft.rfftfreq(n)
        ok = (fr > 1 / 750.0) & (fr < 1 / 30.0)
        sur.append(1.0 / fr[ok][np.argmax(f[ok])])
    sur = np.array(sur)
    print(f"  مسار عشوائى بنفس التقلب: وسيط {np.median(sur):.0f} يومًا · "
          f"الربعيات {np.percentile(sur, 25):.0f}/{np.percentile(sur, 75):.0f}")
    for label, per in PLANET_PERIODS.items():
        band = np.sum(np.abs(np.log(peaks / per)) < np.log(1.10))
        bands = np.sum(np.abs(np.log(sur / per)) < np.log(1.10))
        print(f"    {label:22} حقيقى {band:3} ({100*band/len(peaks):4.1f}%)"
              f" · عشوائى {bands:3} ({100*bands/len(sur):4.1f}%)")


if __name__ == "__main__":
    main()
