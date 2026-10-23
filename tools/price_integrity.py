#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فحص سلامة السلسلة: هل هذا السعر رقمُ السوق؟ أم رقمٌ أعاد الحاسوب بناءه؟

المشكلة التى يحلّها هذا الملف:
    السلسلة المعدَّلة (adjusted) مفيدة للعائد، **قاتلة لعلوم جان** — لأن جان يقرأ
    **الرقم المكتوب** (8729)، لا عائدًا نسبيًّا. وسلسلةٌ ضُربت فى عاملٍ تختفى أرقامها.

والبصمة التى تكشف ذلك بلا حاجة إلى أى مصدر خارجى:

    السوق المصرى يقتبس القرش بمنزلتين: 12.34 جنيهًا. ⇒ **بار بثلاث منازل أو أكثر = رقمٌ محسوب.**

فنقيس لكل سنة: نسبة البارات التى تحمل ≥3 منازل. فإن كانت 100% فالسنة معدَّلة.
وإن كانت 0% فالسنة مقتبَسة كما هى.

والبصمة الثانية: **قفزة التجزئة.** تقسيم السهم يُنتج هبوطًا ليلةً واحدًا (−50%، −33%، −25%).
فى سلسلةٍ خام تبقى القفزة ظاهرة؛ وفى سلسلةٍ معدَّلة تُمحى. والقفزة الظاهرة ليست عيبًا —
هى دليل أن السلسلة خام.

التشغيل:
    python3 tools/price_integrity.py --csv /tmp/egx_clean.csv
    python3 tools/price_integrity.py --csv ... --ticker COMI
"""

import argparse
import collections
import csv


def load(path):
    rows = collections.defaultdict(dict)
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                c = float(r["close"])
            except ValueError:
                continue
            if c <= 0:
                continue
            nd = len(r["close"].split(".")[1]) if "." in r["close"] else 0
            rows[r["ticker"]][r["date"]] = (c, nd)
    return rows


def analyse(series):
    years = collections.defaultdict(lambda: [0, 0])
    for d, (c, nd) in series.items():
        y = d[:4]
        years[y][0] += 1
        years[y][1] += (nd >= 3)
    raw = [y for y, (n, k) in years.items() if n and k / n < 0.05]
    adj = [y for y, (n, k) in years.items() if n and k / n > 0.95]
    dates = sorted(series)
    gaps = []
    for i in range(1, len(dates)):
        a, b = series[dates[i - 1]][0], series[dates[i]][0]
        r = b / a - 1
        if abs(r) > 0.28:
            gaps.append((dates[i], a, b, 100 * r))
    return dates, years, raw, adj, gaps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--ticker")
    ns = ap.parse_args()
    data = load(ns.csv)

    if ns.ticker:
        if ns.ticker not in data:
            raise SystemExit("ليس فى الأرشيف")
        dates, years, raw, adj, gaps = analyse(data[ns.ticker])
        print(f"\n=== {ns.ticker} — {len(dates)} جلسة · {dates[0]} → {dates[-1]} ===\n")
        print(f"  {'السنة':<6}{'بارات':>7}{'بثلاث منازل':>13}{'النسبة':>9}  الحكم")
        for y in sorted(years):
            n, k = years[y]
            print(f"  {y:<6}{n:>7}{k:>13}{100 * k / n:>8.1f}%  "
                  f"{'معدَّلة' if k / n > 0.95 else ('خام' if k / n < 0.05 else 'مختلطة')}")
        print(f"\n  قفزات >28% (تجزئة/إجراء): {len(gaps)}")
        for d, a, b, r in gaps:
            print(f"     {d}  {a:9.2f} → {b:9.2f}   {r:+7.1f}%")
        return

    print("=" * 92)
    print("فحص سلامة السلاسل — أى سهمٍ يصلح لعلوم جان؟")
    print("=" * 92)
    rows = []
    for t, s in data.items():
        if t.upper().startswith("EGX"):
            continue
        dates, years, raw, adj, gaps = analyse(s)
        if len(dates) < 1000:
            continue
        rows.append((len(raw), len(adj), t, len(dates), dates[0], dates[-1], len(gaps)))

    print(f"\n  أسهم فُحصت: {len(rows)}  (≥1000 جلسة)\n")
    print(f"  {'سهم':<9}{'جلسات':>7}{'من':>6}{'سنوات خام':>11}{'سنوات معدَّلة':>14}"
          f"{'قفزات':>8}")
    for r in sorted(rows, reverse=True)[:15]:
        raw, adj, t, n, d0, d1, g = r
        print(f"  {t:<9}{n:>7}{d0[:4]:>6}{raw:>11}{adj:>14}{g:>8}")

    raw_all = [r for r in rows if r[1] == 0 and r[0] >= 5]
    print(f"\n  ⇒ سلاسل خام تمامًا (لا سنة معدَّلة): **{len(raw_all)} سهمًا**")
    print("     وهى الوحيدة التى يصلح عليها قراءة الرقم كما كتبه جان.\n")
    print(f"  {'سهم':<9}{'جلسات':>7}{'سنوات خام':>11}{'قفزات':>8}")
    for r in sorted(raw_all, reverse=True)[:12]:
        raw, adj, t, n, d0, d1, g = r
        print(f"  {t:<9}{n:>7}{raw:>11}{g:>8}")
    pure = [r for r in raw_all if r[6] == 0]
    print(f"\n  ⇒ وبلا أى قفزة تجزئة: **{len(pure)} سهمًا** — أنقى ما فى الأرشيف")
    for r in sorted(pure, reverse=True)[:8]:
        raw, adj, t, n, d0, d1, g = r
        print(f"     {t:<9}{n:>7} جلسة · {d0} → {d1}")
    print("""
  ⇒ **والنتيجة التى تخصّ البنوك:** كل سهمٍ مصرفى فى الأرشيف معدَّلٌ فى كل سنواته،
     فلا يمكن اختباره بعلوم جان على هذه البيانات. والمطلوب له سعرٌ خام مقتبَس.
""")


if __name__ == "__main__":
    main()
