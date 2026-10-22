#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
الضبط الثانى على «زمرة التقويم» — §14.3.2 من docs/03-measurement.md

السؤال: هل تزامن زوج من الأسهم فى انعطافاته صفة **خاصة بالزوج** تستمر عبر
الزمن، أم أنه أثر ميكانيكى لشيئين آخرين؟

  (أ) **كثافة السهم:** سهم له 60 انعطافة يتداخل مع كل شىء أكثر من سهم له 12
      — بلا أى محاذاة.
  (ب) **تشابه العوائد:** سهمان يتحركان معًا ينعطفان معًا بالضرورة.

الطريقة: المدى نصفان. لكل زوج يُحسب الرفع (الرفع = المشاهد ÷ المتوقع) فى كل
نصف، ثم يُسأل: هل الزوج المرتفع رفعه فى النصف الأول مرتفع فى الثانى — **بعد**
نزع أثر الكثافة وتشابه العوائد؟

النتيجة (224 سهمًا · 5,669 زوجًا):
    خام +0.208 · بعد الكثافة +0.137 · بعد العوائد +0.114 · بعد الاثنين +0.018
    (العدم 0.000 ± 0.014 · p = 0.18) ⇒ لا شىء يبقى.

الاستعمال:
    python3 tools/egx_pair_control.py --csv /tmp/egx_clean.csv
"""

import argparse
import collections
import csv
import itertools

import numpy as np

# مؤشرات السوق داخل الأرشيف — ليست أسهمًا، وتدخل الزمر كأطراف فتلوّثها.
# كل ما يبدأ بـ EGX مؤشر: EGX30 · EGX70 · EGX100 · EGX30ETF · "EGX30 CAPPED".
def is_index(ticker):
    return ticker.upper().startswith("EGX")


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
    return {t: v for t, v in by.items() if not is_index(t) and len(v) >= min_rows}


def zigzag(prices, th, skip=30):
    """انعطاف = ارتداد بنسبة th عن أقصى/أدنى نقطة، مع تجاهل أول skip صفًا."""
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


def half_pairs(piv, ret, lo, hi, min_pivots=6, min_overlap=200):
    """لكل زوج له تداخل ≥1 فى النصف: (الرفع، ارتباط العوائد، كثافة السهم الأقل)."""
    ids = [t for t in piv if len([d for d in piv[t] if lo <= d < hi]) >= min_pivots]
    P = {t: {d for d in piv[t] if lo <= d < hi} for t in ids}
    span = len({d for t in ids for d in P[t]}) or 1
    out = {}
    for a, b in itertools.combinations(ids, 2):
        expected = len(P[a]) * len(P[b]) / span
        if expected <= 0:
            continue
        common = [d for d in ret[a] if d in ret[b] and lo <= d < hi]
        if len(common) < min_overlap:
            continue
        xa = np.array([ret[a][d] for d in common])
        xb = np.array([ret[b][d] for d in common])
        shared = len(P[a] & P[b])
        out[(a, b)] = (shared / expected, float(np.corrcoef(xa, xb)[0, 1]),
                       min(len(P[a]), len(P[b])), shared)
    return out


def r2(y, cols):
    M = np.column_stack([np.ones_like(y)] + cols)
    beta = np.linalg.lstsq(M, y, rcond=None)[0]
    return 1 - np.var(y - M @ beta) / np.var(y)


def resid(y, cols):
    M = np.column_stack([np.ones_like(y)] + cols)
    return y - M @ np.linalg.lstsq(M, y, rcond=None)[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--since", default="2014-01-01")
    ap.add_argument("--th", type=float, default=0.20)
    ap.add_argument("--min-rows", type=int, default=1000)
    ap.add_argument("--shuffles", type=int, default=1000)
    a = ap.parse_args()

    data = load(a.csv, a.since, a.min_rows)
    piv, ret = {}, {}
    for t, v in data.items():
        ds = sorted(v)
        piv[t] = set(ds[i + 30] for i in zigzag([v[d] for d in ds], a.th))
        ret[t] = {d: np.log(v[d] / v[ds[i - 1]])
                  for i, d in enumerate(ds) if i > 0 and v[ds[i - 1]] > 0}

    A = half_pairs(piv, ret, "2014-01-01", "2020-01-01")
    B = half_pairs(piv, ret, "2020-01-01", "2026-01-01")
    common = [k for k in A if k in B and A[k][3] >= 1 and B[k][3] >= 1]

    y1 = np.array([np.log1p(A[k][0]) for k in common])
    y2 = np.array([np.log1p(B[k][0]) for k in common])
    c1 = np.array([A[k][1] for k in common])
    c2 = np.array([B[k][1] for k in common])
    d1 = np.log([A[k][2] for k in common])
    d2 = np.log([B[k][2] for k in common])

    print(f"أسهم: {len(data)} · أزواج مشتركة: {len(common):,}\n")
    print("═══ ارتباط النصفين بعد نزع كل ملوِّث ═══")
    for tag, cols in [("خام", []),
                      ("الكثافة", [d2]),
                      ("تشابه العوائد", [c2]),
                      ("الاثنان", [d2, c2])]:
        r = np.corrcoef(resid(y1, cols), resid(y2, cols))[0, 1]
        print(f"  {tag:16} r = {r:+.3f}")

    rng = np.random.default_rng(99)
    r1, r2_ = resid(y1, [d2, c2]), resid(y2, [d2, c2])
    obs = np.corrcoef(r1, r2_)[0, 1]
    sh = np.array([np.corrcoef(r1, r2_[rng.permutation(len(r2_))])[0, 1]
                   for _ in range(a.shuffles)])
    print(f"\n  العدم: {sh.mean():+.4f} ± {sh.std():.4f} · "
          f"p = {np.mean(np.abs(sh) >= abs(obs)):.2f}")

    print("\n═══ هل يضيف «التقويم» فوق الترابط والكثافة؟ ═══")
    print(f"  y2 ~ (كثافة + ترابط)      R² = {r2(y2, [d2, c2]):.4f}")
    print(f"     + y1 (التقويم)         R² = {r2(y2, [d2, c2, y1]):.4f}")
    print(f"  y1 ~ (كثافة + ترابط)      R² = {r2(y1, [d1, c1]):.4f}")
    print(f"     + y2                   R² = {r2(y1, [d1, c1, y2]):.4f}")


if __name__ == "__main__":
    main()
