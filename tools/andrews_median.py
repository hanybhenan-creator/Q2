#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خط أندروز الوسيط — تنفيذُ الكتاب حرفًا، واختبارُ ادّعائه «٨٠%».

المصدر: Patrick Mikula, *The Best Trendline Methods of Alan Andrews and Five
New Trendline Techniques*, ٩٦ ص — نسخةٌ نصّية كاملة (٨١٬٧٠٨ حرفًا)، قُرئت صفحةً
صفحة. والصفحات المذكورة أدناه هى صفحات الكتاب نفسه.

البناء (ص٦) حرفًا:
  «Three pivots are needed to draw a Median Line. Two of the pivots must be the
   high and low of a price swing. The mid-point between these first two points
   must be calculated … **The range between the high and low is divided by two
   and added to the low value. The same is done for the amount of time** …
   a third pivot which occurs before the price swing … is the Median Line
   starting point. The Median Line is drawn by connecting the starting pivot A
   and the middle of the B-C price swing.»

والادّعاء المُختبَر (ص٧ · ص٨ · ص٥٨):
  «Andrews believed that the price returns to the Median Line **about 80%** of
   the time.» · «Principle 1: … the price should return to the Median Line
   **approximately 80 percent** of the time.»

والضابط الداخلى (من الكتاب نفسه، ص١٣): «One is a dotted line connecting pivots
A and B. This is the upper **Trigger Line** … A and C … the lower Trigger Line.»
  ⇒ فالخطان A–B وA–C موجودان فى الكتاب كخطَّى تنبيه. وهما **حالتان حدّيتان**
     لنفس التركيب: النقطة الوسيطة عند m = 0 و m = 1. فإن لم يتفوّق الوسيط
     (m = 0.5) عليهما، فليس «المركز» هو السبب — بل مجرّدُ كون الخط يمرّ بسوينج C.

التشغيل:
    python3 -u tools/andrews_median.py [--csv /tmp/egx_clean.csv] [--pct 0.05]
"""

import argparse
import collections
import csv
import datetime as dt
import statistics
import sys

CLEAN = ["ARCC", "CCAP", "CLHO", "ELSH", "EMFD", "IDRE", "ISMA",
         "KZPC", "MTIE", "ORAS", "SUGR", "TMGH"]


def hdr(t):
    print("\n" + "=" * 86)
    print(" " + t)
    print("=" * 86)


def load(path):
    s = collections.defaultdict(dict)
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["ticker"] not in CLEAN:
                continue
            try:
                d = dt.date.fromisoformat(r["date"][:10])
                hi, lo = float(r["high"]), float(r["low"])
            except (ValueError, KeyError):
                continue
            if lo > 0 and hi > 0 and hi >= lo:
                s[r["ticker"]][d] = (lo, hi)
    return s


def zigzag(bars, pct):
    """نقاط الانعطاف: قمة/قاع يتغيّر عندهما الاتجاه بمقدار pct."""
    piv = []
    if not bars:
        return piv
    trend, ext_i = 1, 0
    for i in range(1, len(bars)):
        hi, lo = bars[i][1], bars[i][0]
        eh, el = bars[ext_i][1], bars[ext_i][0]
        if trend > 0:
            if hi >= eh:
                ext_i = i
            elif lo <= eh * (1 - pct):
                piv.append((ext_i, 1))
                trend, ext_i = -1, i
        else:
            if lo <= el:
                ext_i = i
            elif hi >= el * (1 + pct):
                piv.append((ext_i, -1))
                trend, ext_i = 1, i
    piv.append((ext_i, trend))
    return piv


def median_line(pa, pb, pc, m):
    """ميلُ الخط من A عبر النقطة m من السوينج B-C (بالوحدات: بار/سعر)."""
    tm = pb[0] + m * (pc[0] - pb[0])
    pm = pb[1] + m * (pc[1] - pb[1])
    if abs(tm - pa[0]) < 1e-9:
        return None
    return (pm - pa[1]) / (tm - pa[0])


def test_stock(bars, pct, m, horizon_mult=1.0):
    """يعيد: (عدد الحالات، عدد التلامس، عدد التلامس داخل النطاق، أعمار)."""
    piv = zigzag(bars, pct)
    hits = inzone = tot = 0
    piv_on = 0
    for k in range(2, len(piv)):
        ia, _ = piv[k - 2]
        ib, _ = piv[k - 1]
        ic, dip = piv[k]
        if ic - ib < 2 or ib - ia < 2:
            continue
        ta, pa_p = ia, (bars[ia][1] if piv[k - 2][1] > 0 else bars[ia][0])
        tb, pb_p = ib, (bars[ib][1] if piv[k - 1][1] > 0 else bars[ib][0])
        tc, pc_p = ic, (bars[ic][1] if dip > 0 else bars[ic][0])
        s = median_line((ta, pa_p), (tb, pb_p), (tc, pc_p), m)
        if s is None:
            continue
        zone = int(max(abs(tb - ta), abs(tc - tb)) * horizon_mult)
        if zone < 2:
            continue
        tot += 1
        hit_at = None
        for j in range(tc + 1, min(len(bars), tc + zone + 1)):
            line = pa_p + s * (j - ta)
            if bars[j][0] <= line <= bars[j][1]:
                hit_at = j
                break
        if hit_at is not None:
            hits += 1
            inzone += 1
        # هل وقع الانعطاف التالى قريبًا من الخط؟
        if k + 1 < len(piv):
            nxt, ntyp = piv[k + 1]
            line = pa_p + s * (nxt - ta)
            px = bars[nxt][1] if ntyp > 0 else bars[nxt][0]
            if line and abs(px - line) / max(1e-9, line) <= 0.03:
                piv_on += 1
    return tot, hits, inzone, piv_on


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="/tmp/egx_clean.csv")
    ap.add_argument("--pct", type=float, default=0.05)
    a = ap.parse_args()

    hdr("١. البناء — كما هو فى ص٦، على مثالٍ مُرقَّم")
    print("""  ثلاث نقاط انعطاف: A (قبل السوينج) · B و C (طرفا السوينج).
  النقطة الوسيطة M = منتصف B–C فى **السعر وفى الزمن** معًا:
      M(سعر) = B + (C − B) / 2        M(زمن) = B + (C − B) / 2
  والخط الوسيط = الخط من A عبر M، ممتدًّا.
  والخطان الموازيان: من B ومن C ⇒ «الشوكة» (ص١٣).""")

    data = load(a.csv)
    stocks = [(t, [x for _, x in sorted(v.items())])
              for t, v in sorted(data.items()) if len(v) > 400]

    t0, b0 = stocks[0]
    piv = zigzag(b0, a.pct)
    if len(piv) >= 3:
        ia, ty_a = piv[-3]
        ib, ty_b = piv[-2]
        ic, ty_c = piv[-1]
        pa_p = b0[ia][1] if ty_a > 0 else b0[ia][0]
        pb_p = b0[ib][1] if ty_b > 0 else b0[ib][0]
        pc_p = b0[ic][1] if ty_c > 0 else b0[ic][0]
        tm, pm = (ib + ic) / 2, (pb_p + pc_p) / 2
        print(f"\n  مثال: {t0} — آخر ثلاث نقاط ({a.pct:.0%} انعطاف)")
        print(f"    A = بار {ia:>5} · سعر {pa_p:>8.2f}")
        print(f"    B = بار {ib:>5} · سعر {pb_p:>8.2f}")
        print(f"    C = بار {ic:>5} · سعر {pc_p:>8.2f}")
        print(f"    M = بار {tm:>5.1f} · سعر {pm:>8.2f}   ← منتصف B–C فى الاثنين")
        s = median_line((ia, pa_p), (ib, pb_p), (ic, pc_p), 0.5)
        print(f"    ميل الخط الوسيط = {s:+.4f} سعر/بار")
        print(f"    سعره بعد ٥٠ بارًا من C = {pa_p + s*(ic+50-ia):.2f}")

    hdr("٢. ادّعاء الكتاب: «٨٠% من المرات» — القياس")
    print(f"  الانعطاف {a.pct:.0%} · النطاق = أكبر السوينجين (A–B أو B–C) بارًا\n")
    print(f"  {'السهم':>7} {'حالات':>7} {'لمست الوسيط':>13} {'النسبة':>8} "
          f"{'انعطاف على الخط':>17}")
    tot = hit = pon = 0
    for t, bars in stocks:
        n, h, _, p = test_stock(bars, a.pct, 0.5)
        if n < 5:
            continue
        tot += n; hit += h; pon += p
        print(f"  {t:>7} {n:>7} {h:>13} {100*h/n:>7.1f}% "
              f"{100*p/max(1,n):>16.1f}%")
    rate = 100.0 * hit / max(1, tot)
    print(f"\n  المجموع: {hit}/{tot} = **{rate:.1f}%**  (ادّعاء الكتاب 80%)")
    print(f"  وانعطافٌ على الخط بسماحية 3%: {100*pon/max(1,tot):.1f}%")

    hdr("٣. الضابط الداخلى — الوسيط مقابل خطَّى التنبيه (ص١٣)")
    print("""  الخط من A عبر النقطة m من السوينج B–C:
     m = 0.0  ⇒  الخط A–B  = **خط التنبيه العلوى**
     m = 0.5  ⇒  **الخط الوسيط** (ادّعاء ٨٠%)
     m = 1.0  ⇒  الخط A–C  = **خط التنبيه السفلى**
  فإن تساوت النسب فليس «المركز» هو السبب، بل مرورُ الخط بالسوينج C.\n""")
    print(f"  {'m':>5} {'الخط':>16} {'حالات':>7} {'لمسات':>8} {'النسبة':>8}")
    rows = []
    for m, name in ((0.0, "تنبيه A–B"), (0.25, "ربع"), (0.5, "**الوسيط**"),
                    (0.75, "ثلاثة أرباع"), (1.0, "تنبيه A–C")):
        T = H = 0
        for t, bars in stocks:
            n, h, _, _ = test_stock(bars, a.pct, m)
            T += n
            H += h
        rows.append((m, name, T, H, 100.0 * H / max(1, T)))
        print(f"  {m:>5.2f} {name:>16} {T:>7} {H:>8} {100.0*H/max(1,T):>7.1f}%")
    best = max(rows, key=lambda r: r[4])
    print(f"\n  ⇒ الأعلى: m = {best[0]} ({best[4]:.1f}%) · الوسيط (m=0.5): {rows[2][4]:.1f}%")

    hdr("٤. «نطاق الانعطاف» (ص٥٩) — هل يصل قبل انتهاء النطاق؟")
    print("""  القاعدة: من C، للأمام عددَ بارات **أكبر السوينجين**، «the price usually
  reaches the Median Line before the end of the Median Line Pivot Zone».
  فقِسْ: هل اللمسة داخل النطاق أم خارجه؟""")
    T = H = 0
    for t, bars in stocks:
        n, h, iz, _ = test_stock(bars, a.pct, 0.5)
        T += n; H += iz
    print(f"  اللمسات داخل النطاق: {H}/{T} = {100.0*H/max(1,T):.1f}%")

    hdr("٤.١ الأفق — هل الادّعاء يصحّ إن أطلنا الانتظار؟")
    print("  النسبة عند مضاعفات النطاق (m = 0.5):\n")
    print(f"  {'الأفق':>10} {'حالات':>7} {'لمسات':>8} {'النسبة':>8}")
    for mult in (1.0, 2.0, 4.0, 8.0):
        T = H = 0
        for t, bars in stocks:
            n, h, _, _ = test_stock(bars, a.pct, 0.5, horizon_mult=mult)
            T += n; H += h
        print(f"  {mult:>8.0f}× {T:>7} {H:>8} {100.0*H/max(1,T):>7.1f}%")
    print("""
  ⇒ فإن ارتفعت النسبة مع الأفق فهذا **ليس إنجازًا للخط**: أى خطٍّ يلمسه السعر
     إن انتظرتَ طويلًا. والادّعاء المفيد هو الوصول **قبل** انتهاء النطاق.""")

    hdr("٥. الحكم")
    print(f"""  ادّعاء أندروز/ميكولا (ص٧ · ص٨ · ص٥٨): **٨٠%**.
  المقيس على ١٢ سهمًا مصريًّا: **{rate:.1f}%**.
  والضابط: أفضل نقطة هى m = {best[0]} بنسبة {best[4]:.1f}% — أى أن اختيار
  «المنتصف» **{'يتفوّق' if rows[2][4] >= best[4]-0.5 else 'لا يتفوّق'}** على بقية النقاط.

  ⇒ فالرقم ٨٠% **{'يُقارَب' if abs(rate-80) < 8 else 'لا يُقارَب'}**، والسؤال الأهمّ:
     هل النجاح منسوبٌ إلى **المركز** الذى يسمّيه أندروز «قانون الفيزياء» (ص٧)،
     أم إلى أن أىَّ خطٍّ يمرّ بسوينج C يلمسه السعر داخل نطاقٍ قصير؟""")
    print("  والجواب فى الجدول ٣ لا فى الكلام.")


if __name__ == "__main__":
    main()
