#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تحميل أرشيف EGX بصيغة MetaStock وتنقيته إلى **نسخة واحدة أحدث**.

الشكل: <TICKER>,<PER>,<DTYYYYMMDD>,<TIME>,<OPEN>,<HIGH>,<LOW>,<CLOSE>,<VOL>,<OPENINT>

والملف الواصل ثمانية أجزاء، لكنها ليست تقسيمًا متسلسلًا: هى **ثلاث نسخ
من التصدير نفسه** كُتبت فوق بعضها ثم قُطعت عند 24 ميجابايت. فالسهم الواحد
يظهر فى ثلاث نسخ تنتهى فى 2025-10-22 و2025-10-26 و2025-10-27.

فالقاعدة: لكل (سهم، تاريخ) تُؤخذ الصفوف من **النسخة التى تنتهى فى أحدث تاريخ**
لهذا السهم. والنسخ الأقدم لا تُحذف بالتاريخ، بل تُستبعد بالهوية — لأنها قد
تحمل تصحيحًا مختلفًا للأسعار (قياس §5.4).

الاستعمال:
    python3 tools/egx_load.py --dir /home/user/data/egx-ohlcv --out /tmp/egx_clean.csv
    python3 tools/egx_load.py --dir ... --audit
"""

import argparse
import collections
import csv
import datetime
import glob
import os
import sys

COLS = ["ticker", "date", "open", "high", "low", "close", "volume"]


def _iter_rows(paths):
    for path in paths:
        with open(path, encoding="utf-8-sig", errors="replace") as fh:
            fh.readline()  # العنوان
            for line in fh:
                p = line.rstrip("\r\n").split(",")
                if len(p) < 9 or not p[2].isdigit() or len(p[2]) != 8:
                    continue
                try:
                    d = datetime.date(int(p[2][:4]), int(p[2][4:6]), int(p[2][6:]))
                except ValueError:
                    continue
                yield (p[0], d, float(p[4]), float(p[5]), float(p[6]),
                       float(p[7]), float(p[8]))


def load_newest(paths):
    """يعيد {(ticker,date): row} من النسخة الأحدث لكل سهم، مع تقرير النسخ."""
    # 1) نهاية كل (سهم، ملف) — تحدد أى ملف يحمل أى نسخة
    ends = collections.defaultdict(dict)
    for t, d, *_ in _iter_rows(paths):
        cur = ends[t].get(_src[0])
        if cur is None or d > cur:
            ends[t][_src[0]] = d

    best = {}
    for t, parts in ends.items():
        if parts:
            best[t] = max(parts, key=lambda k: (parts[k], k))

    out = {}
    order = {p: i for i, p in enumerate(paths)}
    for t, d, o, h, l, c, v in _iter_rows(paths):
        if _src[0] != best.get(t):
            continue
        key = (t, d)
        if key not in out or order[_src[0]] >= 0:
            out[key] = (o, h, l, c, v)
    return out, ends, best


_src = [None]


def audit(rows):
    n = len(rows)
    if not n:
        print("لا صفوف")
        return
    openz = sum(1 for v in rows.values() if v[0] == 0)
    badh = sum(1 for v in rows.values() if v[1] < max(v[0], v[3]) - 1e-6)
    badl = sum(1 for v in rows.values() if v[2] > min(v[0], v[3]) + 1e-6)
    nonpos = sum(1 for v in rows.values() if v[3] <= 0 or v[1] <= 0 or v[2] <= 0)
    volz = sum(1 for v in rows.values() if v[4] == 0)
    fri = sat = 0
    for (t, d) in rows:
        if d.weekday() == 4:
            fri += 1
        elif d.weekday() == 5:
            sat += 1
    tick = {t for t, _ in rows}
    ds = [d for _, d in rows]
    print("=" * 68)
    print("  فحص النسخة الواحدة")
    print("=" * 68)
    print(f"  الصفوف            {n:,}")
    print(f"  الأسهم            {len(tick)}")
    print(f"  المدى             {min(ds)} → {max(ds)}")
    print(f"  OPEN = 0          {openz:,}  ({100 * openz / n:.2f}%)")
    print(f"  high < max(o,c)   {badh:,}  ({100 * badh / n:.2f}%)")
    print(f"  low  > min(o,c)   {badl:,}  ({100 * badl / n:.2f}%)")
    print(f"  سعر ≤ 0           {nonpos:,}")
    print(f"  حجم = 0           {volz:,}  ({100 * volz / n:.2f}%)")
    print(f"  جلسات جمعة/سبت    {fri} / {sat}")

    per_ticker = collections.Counter(t for t, _ in rows)
    sizes = sorted(per_ticker.values())
    print(f"  صفوف/سهم          وسيط {sizes[len(sizes) // 2]:,} · أدنى {sizes[0]:,} · أعلى {sizes[-1]:,}")
    print(f"  أسهم بأقل من 100 صف  {sum(1 for v in sizes if v < 100)}")
    return {"rows": n, "open0": openz, "badh": badh, "badl": badl}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out")
    ap.add_argument("--audit", action="store_true")
    ns = ap.parse_args()

    paths = sorted(glob.glob(os.path.join(ns.dir, "part*.csv")))
    if not paths:
        sys.exit("لا ملفات part*.csv")

    # التمرير على الملفات مع تتبّع الملف الحالى
    ends = collections.defaultdict(dict)
    for path in paths:
        with open(path, encoding="utf-8-sig", errors="replace") as fh:
            fh.readline()
            for line in fh:
                p = line.rstrip("\r\n").split(",")
                if len(p) < 9 or not p[2].isdigit() or len(p[2]) != 8:
                    continue
                try:
                    d = datetime.date(int(p[2][:4]), int(p[2][4:6]), int(p[2][6:]))
                except ValueError:
                    continue
                cur = ends[p[0]].get(path)
                if cur is None or d > cur:
                    ends[p[0]][path] = d
    best = {t: max(parts, key=lambda k: (parts[k], k)) for t, parts in ends.items() if parts}

    rows = {}
    for path in paths:
        with open(path, encoding="utf-8-sig", errors="replace") as fh:
            fh.readline()
            for line in fh:
                p = line.rstrip("\r\n").split(",")
                if len(p) < 9 or not p[2].isdigit() or len(p[2]) != 8:
                    continue
                t = p[0]
                if best.get(t) != path:
                    continue
                try:
                    d = datetime.date(int(p[2][:4]), int(p[2][4:6]), int(p[2][6:]))
                    rows[(t, d)] = (float(p[4]), float(p[5]), float(p[6]),
                                    float(p[7]), float(p[8]))
                except ValueError:
                    continue

    gens = collections.Counter(max(parts.values()) for parts in ends.values() if parts)
    print("النسخ المكتشفة (حسب نهاية كل سهم):")
    for d, k in sorted(gens.items()):
        print(f"   تنتهى {d}  ←  {k} سهمًا")
    print(f"مصدر النسخة المختارة: {len(set(best.values()))} ملفًا\n")

    audit(rows)

    if ns.out:
        rows_sorted = sorted(rows.items())
        with open(ns.out, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(COLS)
            for (t, d), v in rows_sorted:
                w.writerow([t, d.isoformat(), v[0], v[1], v[2], v[3], v[4]])
        print(f"\nكُتب {len(rows):,} صفًا إلى {ns.out}")


if __name__ == "__main__":
    main()
