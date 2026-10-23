#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
هل يدور النشاط بين الأسهم؟ — §17.3 من docs/04-selection-engine.md

يقول جان إن الأسهم «تقود السوق فى أوقات، وتموت فى أوقات أخرى». فإن صحّ
ذلك، فالنشاط يدور: السهم النشط هذا العام يخفت بعده. وإن لم يصحّ، فالنشاط
**سِمة ثابتة** — وعندئذ لا يحتاج اختيار السهم مسحًا يوميًا، بل تصنيفًا
يُحدَّث سنويًا. وهذا هو الفرق بين ماسح رقمى وطريقة.

المقياس: قيمة التداول الوسيطة (إغلاق × حجم) لكل سهم فى كل سنة، ثم ارتباط
الرتب (سبيرمان) بين سنة وأخرى، ومصفوفة الانتقال بين خمسيات السيولة.

النتيجة على 2014–2025: ثبات لا دوران — +0.888 سنة/سنة، والقطر يهيمن.

التشغيل:
    python3 tools/egx_activity_rotation.py --csv /tmp/egx_clean.csv
"""

import argparse
import collections
import csv

import numpy as np


def load(path, since, min_rows):
    by = collections.defaultdict(dict)
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["date"] < since:
                continue
            try:
                c, v = float(r["close"]), float(r["volume"])
            except ValueError:
                continue
            if c > 0 and v >= 0:
                by[r["ticker"]][r["date"]] = c * v
    return {t: v for t, v in by.items()
            if not t.upper().startswith("EGX") and len(v) >= min_rows}


def turnover_median(series, year, min_days=120):
    vals = [v for d, v in series.items() if d.startswith(str(year)) and v > 0]
    if len(vals) < min_days:
        return None
    return float(np.median(vals))


def rank(a):
    return np.argsort(np.argsort(a)).astype(float)


def spearman(a, b):
    return float(np.corrcoef(rank(a), rank(b))[0, 1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--since", default="2014-01-01")
    ap.add_argument("--min-rows", type=int, default=1000)
    ap.add_argument("--top", type=int, default=20)
    ns = ap.parse_args()

    data = load(ns.csv, ns.since, ns.min_rows)
    years = sorted({int(d[:4]) for v in data.values() for d in v})
    print(f"أسهم: {len(data)} · سنوات: {years[0]}–{years[-1]}")

    print("\n═══ ارتباط الرتب بين سنة وسنة (قيمة التداول الوسيطة) ═══")
    for gap in (1, 2, 3):
        rs = []
        for y in years[:-gap] if gap <= len(years) else []:
            xs, ys = [], []
            for t, s in data.items():
                a = turnover_median(s, y)
                b = turnover_median(s, y + gap)
                if a and b:
                    xs.append(a)
                    ys.append(b)
            if len(xs) >= 40:
                rs.append(spearman(np.array(xs), np.array(ys)))
        if rs:
            print(f"  مسافة {gap} سنة: وسط {np.mean(rs):+.3f} "
                  f"(مدى {min(rs):+.2f}..{max(rs):+.2f} · {len(rs)} انتقالًا)")

    print("\n═══ الانتقال بين خمسيات السيولة (سنة → التالية) ═══")
    M = np.zeros((5, 5))
    for y in years[:-1]:
        xs, ys = [], []
        for t, s in data.items():
            a = turnover_median(s, y)
            b = turnover_median(s, y + 1)
            if a and b:
                xs.append(a)
                ys.append(b)
        if len(xs) < 40:
            continue
        xs, ys = np.array(xs), np.array(ys)
        qx = np.minimum((rank(xs) / len(xs) * 5).astype(int), 4)
        qy = np.minimum((rank(ys) / len(ys) * 5).astype(int), 4)
        for i, j in zip(qx, qy):
            M[i, j] += 1
    M = M / np.clip(M.sum(axis=1, keepdims=True), 1, None)
    for i in range(5):
        print("  " + " ".join(f"{100 * M[i, j]:4.0f}" for j in range(5)))
    print("  (القطر المهيمن = ثبات، لا دوران)")

    print(f"\n═══ أعلى {ns.top} سهمًا سيولةً: كم يبقى سنويًا؟ ═══")
    tops = {}
    for y in years:
        vals = sorted(((turnover_median(s, y), t) for t, s in data.items()
                       if turnover_median(s, y)), reverse=True)
        tops[y] = {t for _, t in vals[:ns.top]}
    for y in years[:-1]:
        if tops.get(y) and tops.get(y + 1):
            print(f"  {y}→{y + 1}: بقى {len(tops[y] & tops[y + 1])} من {ns.top}")


if __name__ == "__main__":
    main()
