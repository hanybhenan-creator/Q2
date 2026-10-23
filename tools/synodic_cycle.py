#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
دورة العشرين — اقتران المشترى وزحل، ودرجته السينودية، ومواضع الانعطاف.

المستخدم نبّه نبّهًا صحيحًا: بدلًا من انتظار دورةٍ طويلةٍ تكتمل خمس مرّات،
تُستعمل **الدرجة السينودية** — وهى متاحة **كل يوم**. فدورة العشرين لا تحتاج
إلى عشرين سنةٍ تُنتظر، بل إلى **إحداثىّ طور** يُحسب لكل جلسة.

    Ψ = (طول زحل − طول المشترى) mod 360     [مركزي أرضى]
    Ψ = 0    اقتران            Ψ = 180  مقابلة
    Ψ = 90   تربيع أول         Ψ = 270  تربيع رابع

وهو بعينه ما ذكره المستخدم: ٠ · ٩٠ · ١٨٠ · ٢٧٠.

ويُحسم أولًا سؤال «أى اقترانٍ هو العشرينى؟» بالأرقام لا بالذاكرة:
    المشترى–زحل  ≈ 19.86 سنة   ← هو العشرينى
    المشترى–المريخ ≈ 2.24 سنة  (ويُظنّ خطأً عشرينًا)

والضابط — وهو الأهم: **الدرجة السينودية ليست موزّعة بانتظام فى الزمن**، لأن
الكوكبين يرتدّان. فمن استعمل ضابطًا منتظمًا وجد «تجمّعًا» هو أثر التقويم لا
أثر الفلك. والضابط الصحيح: **أيام تداول عشوائية من نفس التقويم**.

التشغيل:
    python3 tools/synodic_cycle.py
"""

import argparse
import collections
import csv
import datetime as dt
import math
import os
import random
import statistics
import sys

import swisseph as swe

swisseph_ok = True
swe.set_ephe_path(None)

LINE = "=" * 84
CLEAN = ["ARCC", "CCAP", "CLHO", "ELSH", "EMFD", "IDRE", "ISMA",
         "KZPC", "MTIE", "ORAS", "SUGR", "TMGH"]
W = 20


def hdr(t):
    print("\n" + LINE + "\n " + t + "\n" + LINE)


def lon(name, jd):
    code = {"jupiter": swe.JUPITER, "saturn": swe.SATURN, "mars": swe.MARS}[name]
    x, _ = swe.calc_ut(jd, code, swe.FLG_SWIEPH)
    return x[0] % 360.0


def jd_of(d):
    return swe.julday(d.year, d.month, d.day, 12.0)


def load(path):
    s = collections.defaultdict(list)
    with open(path, newline="", encoding="utf-8", errors="ignore") as f:
        for r in csv.DictReader(f):
            if r["ticker"] not in CLEAN:
                continue
            try:
                d = dt.datetime.strptime(r["date"][:10], "%Y-%m-%d").date()
                c = float(r["close"])
            except (ValueError, KeyError):
                continue
            if c > 0:
                s[r["ticker"]].append((d, c))
    for t in s:
        s[t].sort()
    return s


def pivots(rows, w=W):
    pv = []
    for i in range(w, len(rows) - w):
        seg = rows[i - w:i + w + 1]
        c = rows[i][1]
        if c == max(x[1] for x in seg):
            pv.append((rows[i][0], c, "H"))
        elif c == min(x[1] for x in seg):
            pv.append((rows[i][0], c, "L"))
    alt = []
    for p in pv:
        if not alt or p[2] != alt[-1][2]:
            alt.append(p)
        elif (p[2] == "H" and p[1] > alt[-1][1]) or (p[2] == "L" and p[1] < alt[-1][1]):
            alt[-1] = p
    return alt


PHI = {}


def psi(d, pair="JS"):
    """الدرجة السينودية: ٠ = اقتران."""
    if (d, pair) not in PHI:
        jd = jd_of(d)
        a, b = (lon("jupiter", jd), lon("saturn", jd)) if pair == "JS" \
            else (lon("jupiter", jd), lon("mars", jd))
        PHI[(d, pair)] = (b - a) % 360.0
    return PHI[(d, pair)]


def synodic_period(a_days, b_days):
    return 1.0 / abs(1.0 / a_days - 1.0 / b_days)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="/tmp/egx_clean.csv")
    a = ap.parse_args()
    if not os.path.exists(a.csv):
        sys.exit(f"لا يوجد {a.csv}")

    hdr("٠. أىّ اقترانٍ هو «العشرينى»؟ — بالحساب لا بالذاكرة")
    js = synodic_period(4332.59, 10759.22) / 365.2422
    jm = synodic_period(4332.59, 686.98) / 365.2422
    print(f"  المشترى–زحل  : **{js:6.2f} سنة**   ← هو العشرينى")
    print(f"  المشترى–المريخ: **{jm:6.2f} سنة**   (٢.٢ فقط — ليس عشرينًا)")
    print(f"""
  ⇒ فذاكرتك لم تخطئ فى الجوهر: «اقترانٌ عشرينى» = **المشترى وزحل**. أما
     المريخ فدورته مع المشترى سنتان وربع. والرقم يُحسم بالحساب (`tools/astro_conjunctions.py`
     يعطى الاقترانين الأخيرين: ٢٠٠٠-٠٥ و٢٠٢٠-١٢، بفاصل ٢٠.٦ سنة — أطول من
     المتوسط لأن الاقتران الثلاثى يمتدّ).

  ⇒ **والأهم:** لا حاجة لانتظار خمس دورات. الدرجة السينودية تُحسب **كل يوم**،
     فكلُّ جلسةٍ لها موضعٌ على دائرة الاقتران. هذا هو الطريق القصير.""")

    rows = load(a.csv)
    all_pv = []
    for t in sorted(rows):
        if len(rows[t]) < 400:
            continue
        for d, c, k in pivots(rows[t]):
            all_pv.append((t, d, c, k))
    days = sorted({d for t in rows for d, _ in rows[t]})
    print(f"\n  انعطافات مقيسة: **{len(all_pv)}** · أيام تداول: **{len(days)}**")

    hdr("١. مواضع الانعطاف على دائرة الاقتران (١٢ قطاعًا × ٣٠°)")
    print("  والضابط: أيام تداول عشوائية من **نفس التقويم** — لأن الدرجة")
    print("  السينودية ليست منتظمة فى الزمن (الكوكبان يرتدّان).\n")
    obs = collections.Counter(int(psi(d) // 30) for _, d, _, _ in all_pv)
    n_pv = len(all_pv)
    random.seed(31)
    nulls = collections.defaultdict(list)
    for _ in range(400):
        c = collections.Counter(int(psi(random.choice(days)) // 30) for _ in range(n_pv))
        for k in range(12):
            nulls[k].append(c[k])
    print(f"  {'القطاع':>7} {'درجات':>10} {'انعطاف':>8} {'متوقَّع':>9} {'نسبة':>7} {'z':>7}")
    for k in range(12):
        mu = statistics.mean(nulls[k])
        sd = statistics.pstdev(nulls[k]) or 1
        print(f"  {k*30:>4}-{k*30+29:<3} {k*30:>9}° {obs[k]:>8} {mu:>9.1f} "
              f"{obs[k]/mu:>7.2f} {(obs[k]-mu)/sd:>+7.2f}")

    hdr("٢. النقاط الأربع ٠ · ٩٠ · ١٨٠ · ٢٧٠ — بعرض ±٥°")
    print("  **التصريح:** «إصابة» = الانعطاف داخل ±٥° من إحدى الدرجات الأربع.")
    print("  وهذا ٤٠° من ٣٦٠ = ‎11.1%‎ لو كان التوزيع منتظمًا — وهو ليس كذلك.\n")
    card = [0, 90, 180, 270]

    def near(x, tol=5):
        return any(min(abs(x - c), 360 - abs(x - c)) <= tol for c in card)

    hits = sum(1 for _, d, _, _ in all_pv if near(psi(d)))
    null_hits = []
    for _ in range(400):
        null_hits.append(sum(1 for _ in range(n_pv) if near(psi(random.choice(days)))))
    mu = statistics.mean(null_hits)
    sd = statistics.pstdev(null_hits)
    print(f"  الانعطافات عند النقاط الأربع: **{hits}/{n_pv} = {100*hits/n_pv:.1f}%**")
    print(f"  المتوقَّع من التقويم نفسه : **{mu:.0f}/{n_pv} = {100*mu/n_pv:.1f}%** "
          f"(‎±{sd:.1f}‎)")
    print(f"  z = **{(hits-mu)/sd:+.2f}**")
    print("""
  ⇒ هذا هو الفرق بين ضابطٍ صحيحٍ وضعيف: لو استُعمل ‎11.1%‎ المنتظم لبدا الفرق
     كبيرًا؛ وبضابط التقويم الحقيقى يُقاس الفرق الفعلى.""")

    hdr("٢ب. الحدّ الحاسم — هل الطور شىءٌ غير التقويم؟")
    by_year = collections.defaultdict(list)
    for d in days:
        by_year[d.year].append(psi(d))
    years = sorted(y for y in by_year if len(by_year[y]) > 150)
    mean_psi = [statistics.mean(by_year[y]) for y in years]
    steps = [abs(b - a) for a, b in zip(mean_psi, mean_psi[1:]) if abs(b - a) < 180]
    rate = statistics.median(steps)
    print(f"  حركة الطور Ψ فى السنة: **{rate:.1f}°** (وسيط الفروق بين السنوات)")
    print(f"  ومدى Ψ داخل السنة الواحدة: "
          f"**{statistics.median([max(by_year[y])-min(by_year[y]) for y in years]):.0f}°**")
    print(f"""
  ⇒ **سنة واحدة ≈ قطاعٌ واحد.** فدرجة ٣٠° تعادل نحو ‎{30/rate:.1f}‎ سنة.
     وهذا يعنى أن الطور والتقويم **شىءٌ واحد** على هذا الأرشيف: أى «تجمّعٍ
     عند Ψ» هو **تجمّعٌ فى سنواتٍ بعينها**، ولا سبيل لفصل أحدهما عن الآخر.""")

    print(f"\n  {'السنة':>6} {'متوسط Ψ':>9} {'مداه':>10} {'القطاع':>10}")
    for y in years:
        v = by_year[y]
        print(f"  {y:>6} {statistics.mean(v):>8.1f}° "
              f"{min(v):>4.0f}–{max(v):<4.0f} {int(statistics.mean(v)//30)*30:>8}°")

    top = max(range(12), key=lambda k: obs[k] / max(statistics.mean(nulls[k]), 1e-9))
    yrs = sorted({y for y in years if any(int(psi(d) // 30) == top for d in days
                                         if d.year == y)})
    print(f"""
  ⇒ وأصدق مثال: القطاع الأكثر تجمّعًا هو **{top*30}°–{top*30+29}°** (‎z = {(obs[top]-statistics.mean(nulls[top]))/statistics.pstdev(nulls[top]):+.1f}‎)،
     وهو يقع فى سنوات **{yrs[0]}–{yrs[-1]}** فقط. فالتجمّع «فلكىّ» فى الظاهر،
     وهو **فترةٌ تقويمية** فى الحقيقة. ولو كان الأثر فلكيًّا لتكرّر فى كل دورةٍ
     من دورات العشرين — ولا يوجد فى الأرشيف إلا **دورة ونصف**.""")

    hdr("٣. هل الاتجاه يتبع الطور؟ (متوسط العائد ٢٠ جلسة بعد كل انعطاف)")
    print(f"  {'القطاع':>9} {'عدد':>6} {'متوسط العائد':>13} {'وسيط':>9}")
    fwd = collections.defaultdict(list)
    for t in sorted(rows):
        if len(rows[t]) < 400:
            continue
        idx = {d: i for i, (d, _) in enumerate(rows[t])}
        for d, c, k in pivots(rows[t]):
            i = idx[d]
            if i + 20 < len(rows[t]):
                r = math.log(rows[t][i + 20][1] / c)
                fwd[int(psi(d) // 30)].append(r)
    for k in range(12):
        v = fwd.get(k, [])
        if not v:
            continue
        print(f"  {k*30:>4}-{k*30+29:<3} {len(v):>6} {100*statistics.mean(v):>12.2f}% "
              f"{100*statistics.median(v):>8.2f}%")

    hdr("٤. الحكم")
    print(f"""  ١. الدورة العشرينية = **المشترى–زحل**، ‎{js:.2f}‎ سنة. والمريخ ليس طرفًا فيها.
  ٢. الانعطافات عند ٠/٩٠/١٨٠/٢٧٠: **{100*hits/n_pv:.1f}%** مقابل
     **{100*mu/n_pv:.1f}%** من التقويم نفسه · ‎z = {(hits-mu)/sd:+.2f}‎ ⇒ لا شىء.
  ٣. **والأهم: هذا الاختبار لا يصلح للحكم.** فالطور يتقدّم ‎{rate:.0f}°‎ فى السنة،
     والأرشيف ‎{27/ (360/rate):.1f}‎ دورة فقط. فالطور والتقويم متلازمان، ولا
     يُفصل بينهما. **الحدّ بياناتٌ لا طريقة.**
  ٤. المطلوب للاختبار: ‎٥‎ دورات ‎= {5*js:.0f}‎ سنة ⇒ أرشيفٌ يبدأ قبل **١٩٨٠**
     (أو سوقٌ آخر يُضاف فتُضاعف الملاحظات).""")


if __name__ == "__main__":
    main()
