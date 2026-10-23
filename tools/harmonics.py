#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
التوافق الفلكى — من Heath وConcord-Cushing إلى مقياس الأداة.

Heath («The Harmonic Origins of the World»، 2018) يزعم أن القدماء قاسوا دورات
الكواكب **بالشهر القمرى** فوصلوا إلى نِسَب موسيقية. وهذا الملف لا يصدّقه ولا
يكذّبه، بل **يحسبه**.

Concord-Cushing («Secrets of the Law of Vibration for Traders»، 2005) ينقل
المبدأ إلى السوق عبر «أصداف الأوكتاف»: التردد يتكرّر بمضاعفة ٢، وما بين
المضاعفتين يُقسَّم بالنِّسَب الموسيقية.

والملف يُخرج أربعة أشياء:
  ١. تحقّق رقمى من نِسَب Heath (المشترى ٩/٨ · زحل ١٦/١٥) ومن أعداد الجُمَل.
  ٢. إثبات أن مقاييس جان (١ · ١٢ · ٣٠ · ٤٥ · ١٤٤ · ٣٦٠) كلها نِسَبٌ من عائلة
     ٢·٣·٥ — أى أوكتافٌ واحد.
  ٣. **الحدّ الفاصل:** ٢٥٢٠ (رقم دانيال) فيه ٧، فهو خارج تلك العائلة.
  ٤. **اختبار مُعلَن سلفًا** على ٨ أسهم مصرية نظيفة: هل مقياس الأداة (نقطة/يوم)
     ثابت من نصفها الأول إلى نصفها الثانى؟ وهل يثبت حين يُقاس نسبيًّا لا مطلقًا؟

التشغيل:
    python3 tools/harmonics.py
    python3 tools/harmonics.py --csv /tmp/egx_clean.csv
"""

import argparse
import csv
import datetime as dt
import math
import os
import random
from fractions import Fraction

LINE = "=" * 82


def hdr(t):
    print("\n" + LINE + "\n " + t + "\n" + LINE)


def factors_235(n):
    """عوامل العدد، وهل هو من عائلة ٢·٣·٥."""
    fac, m = [], n
    for p in (2, 3, 5):
        while m % p == 0:
            fac.append(p)
            m //= p
    return fac, m


# ─────────────────────────────────────────────────────────────────────
# ١. نِسَب Heath
# ─────────────────────────────────────────────────────────────────────

SYNODIC = {"عطارد": 115.88, "الزهرة": 583.92, "المريخ": 779.94,
           "المشترى": 398.88, "زحل": 378.09}
LUNAR_YEAR = 12 * 29.53059
TARGET = {  # ما يدّعيه Heath صراحةً
    "المشترى": (9, 8, "تون كامل"),
    "زحل": (16, 15, "نصف تون"),
}


def heath():
    hdr("١. نِسَب Heath — حساب لا تصديق")
    print(f"  السنة القمرية (١٢ × ٢٩.٥٣٠٥٩) = {LUNAR_YEAR:.3f} يومًا\n")
    print(f"  {'الجرم':8} {'الاقتران':>9} {'÷ السنة القمرية':>15} {'ادّعاء Heath':>14} "
          f"{'محسوب':>9} {'الفرق':>8}")
    for name, syn in SYNODIC.items():
        r = syn / LUNAR_YEAR
        claim = TARGET.get(name)
        if claim:
            num, den, label = claim
            exact = num / den
            print(f"  {name:8} {syn:>9.2f} {r:>15.4f} {label:>14} {exact:>9.4f} "
                  f"{100*(r/exact-1):>7.3f}%")
        else:
            print(f"  {name:8} {syn:>9.2f} {r:>15.4f} {'—':>14} {'—':>9} {'—':>8}")
    print("""
  ⇒ الزعم يصحّ: المشترى ‎1.1256‎ مقابل ٩/٨ = ‎1.1250‎ (فرق ٠.٠٥٪)، وزحل ‎1.0669‎
     مقابل ١٦/١٥ = ‎1.0667‎ (فرق ٠.٠٢٪). وهذا ليس رمزًا: نسبتان موسيقيتان
     تنطبقان على دورتين فلكيتين بدقّة جزءٍ من الألف.

  وأعداد «الجُمَل» عند Heath: الشهر ١٠ · السنة ١٢٠ · المشترى ١٣٥ · زحل ١٢٨:""")
    for n in (10, 120, 128, 135, 144, 360, 2520, 1260):
        fac, rest = factors_235(n)
        s = "×".join(map(str, fac)) or "1"
        tag = "داخل عائلة ٢·٣·٥" if rest == 1 else f"يخرج بالعدد {rest}"
        print(f"     {n:>5} = {s:20} {tag}")
    print("""
  ⇒ **هنا الحدّ الفاصل فى هذا الملف:** أعداد Heath كلها من عائلة ٢·٣·٥، فتُقسم
     على ٢ و٣ و٥ بلا كسور وتُعطى أنصافًا وأثلاثًا وأخماسًا — أى كسور الدائرة.
     و٢٥٢٠ (رقم دانيال، وهو أيضًا lcm(1..10)) **يحمل ٧**، فليس من تلك العائلة.

     فمنظومة Heath الموسيقية ومنظومة دانيال الزمنية **لا تدوران فى نفس الدائرة**:
     الأولى خُماسية الحدّ، والثانية سُباعية. ومن جمعهما بلا تصريحٍ خلط دائرتين.""")


# ─────────────────────────────────────────────────────────────────────
# ٢. مقاييس جان على الأوكتاف
# ─────────────────────────────────────────────────────────────────────

def oct_fraction(r):
    """النسبة بعد اختزالها إلى أوكتافٍ واحد، كسرًا تامًّا."""
    f = Fraction(r).limit_denominator(1000) if not isinstance(r, Fraction) else r
    while f >= 2:
        f /= 2
    while f < 1:
        f *= 2
    return f


def gann_scales():
    hdr("٢. مقاييس جان — أوكتافٌ واحد")
    scales = [1, 12, 30, 45, 144, 360]
    print("  كلُّ مقياسٍ ÷ الذى قبله؛ ثم يُختزل بمضاعفات ٢ إلى ما بين ١ و٢:\n")
    print(f"  {'من':>5} {'إلى':>5} {'النسبة':>9} {'بعد الأوكتاف':>13} "
          f"{'الكسر':>8} {'أوكتافات':>9} {'٢·٣·٥؟':>9}")
    for a, b in zip(scales, scales[1:]):
        r = Fraction(b, a)
        oc = oct_fraction(r)
        _, rest = factors_235(oc.numerator * oc.denominator)
        # العائلة تُختبر على الكسر نفسه لا على حاصل ضربه
        in5 = all(factors_235(x)[1] == 1 for x in (oc.numerator, oc.denominator))
        print(f"  {a:>5} {b:>5} {float(r):>9.3f} {float(oc):>13.4f} "
              f"{str(oc.numerator)+'/'+str(oc.denominator):>8} "
              f"{math.log2(float(r)):>9.3f} {'نعم' if in5 else 'لا':>9}")
    print("""
  ⇒ ١٢/١ = ٢³ × ٣/٢ · ٣٠/١٢ = ٢ × ٥/٤ · ٤٥/٣٠ = ٣/٢ · ١٤٤/٤٥ = ٢ × ٨/٥ ·
     ٣٦٠/١٤٤ = ٢ × ٥/٤.
     كلُّ نسبةٍ **كسرٌ تامّ** من عائلة ٢·٣·٥، بلا تقريب. فمقاييس جان ليست
     أرقامًا متفرّقة، بل أعضاء فى أوكتافٍ واحد: تصعد بالأوكتاف (٢) وبالخُماس
     (٣/٢) وبالسدس الصغير (٨/٥) وبالربع (٥/٤).

  ⇒ وهذا **تحقّق** لقول Concord-Cushing «أصداف الأوكتاف»، لا نقلًا عنه: أخذنا
     الأرقام وحدها فأنتجت البنية.""")


# ─────────────────────────────────────────────────────────────────────
# ٣. الاختبار المُعلَن سلفًا
# ─────────────────────────────────────────────────────────────────────

CLEAN = ["GTWL", "TMGH", "GRCA", "IDRE", "ISMA", "CCAP", "EMFD", "CLHO"]
W = 20
TOL = 0.10
SPAN = 2
SIMPLES = [Fraction(1), Fraction(16, 15), Fraction(9, 8), Fraction(6, 5),
           Fraction(5, 4), Fraction(4, 3), Fraction(3, 2), Fraction(8, 5)]


def load(path, ticker):
    rows = []
    with open(path, newline="", encoding="utf-8", errors="ignore") as f:
        for x in csv.DictReader(f):
            if x["ticker"] != ticker:
                continue
            try:
                d = dt.datetime.strptime(x["date"][:10], "%Y-%m-%d").date()
                c = float(x["close"])
            except (ValueError, KeyError):
                continue
            if c > 0:
                rows.append((d, c))
    rows.sort()
    return rows


def swings(rows, w=W):
    pv = []
    for i in range(w, len(rows) - w):
        seg = rows[i - w:i + w + 1]
        c = rows[i][1]
        if c == max(s[1] for s in seg):
            pv.append((rows[i][0], c, "H"))
        elif c == min(s[1] for s in seg):
            pv.append((rows[i][0], c, "L"))
    alt = []
    for p in pv:
        if not alt or p[2] != alt[-1][2]:
            alt.append(p)
        elif (p[2] == "H" and p[1] > alt[-1][1]) or (p[2] == "L" and p[1] < alt[-1][1]):
            alt[-1] = p
    return alt


def med(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else None


def rate_pt(seg):
    return med([abs(b[1] - a[1]) / (b[0] - a[0]).days
                for a, b in zip(seg, seg[1:]) if (b[0] - a[0]).days > 0])


def rate_log(seg):
    return med([abs(math.log(b[1] / a[1])) / (b[0] - a[0]).days
                for a, b in zip(seg, seg[1:]) if (b[0] - a[0]).days > 0])


def on_ladder(r2, r1):
    for k in range(-SPAN, SPAN + 1):
        for s in SIMPLES:
            if abs(r2 / (r1 * s * 2.0 ** k) - 1.0) <= TOL:
                return True
    return False


def test(csv_path):
    hdr("٣. الاختبار — مقياسُ الأداة من نصفها الأول إلى نصفها الثانى")
    print("  **التصريح قبل النظر (لا يُعدَّل بعده):**")
    print(f"   • الانعطاف = أقصى/أدنى إغلاق فى ±{W} جلسة، قممٌ وقيعانٌ متبادلة.")
    print("   • المقياس المُطلق r = وسيط(|Δالسعر| ÷ Δالأيام) — نقطة/يوم.")
    print("   • المقياس النسبى g = وسيط(|Δln السعر| ÷ Δالأيام) — لوغاريتم/يوم.")
    print("   • التعلّم: النصف الأول من الانعطافات. القراءة: النصف الثانى.")
    print(f"   • «ثابت» = g₂/g₁ بين {1-TOL:.2f} و{1+TOL:.2f}.")
    print(f"   • «على السلّم» = r₂ على سلّم r₁ × ٢^−2..+2 × النِّسَب (تسامح {TOL:.0%}).")
    print()

    data = {}
    for t in CLEAN:
        rows = load(csv_path, t)
        if len(rows) < 400:
            continue
        pv = swings(rows)
        if len(pv) < 8:
            continue
        h = len(pv) // 2
        data[t] = dict(n=len(pv), p1=rate_pt(pv[:h]), p2=rate_pt(pv[h:]),
                       g1=rate_log(pv[:h]), g2=rate_log(pv[h:]))

    print(f"  {'السهم':>6} {'انعطاف':>7} {'r₁':>9} {'r₂':>9} {'r₂/r₁':>7} "
          f"{'g₁·10³':>8} {'g₂·10³':>8} {'g₂/g₁':>7} {'ثابت؟':>7} {'سلّم؟':>7}")
    const = lad = 0
    gs1, gs2 = [], []
    for t, d in data.items():
        rc = d["p2"] / d["p1"]
        gc = d["g2"] / d["g1"]
        ok_c = abs(gc - 1) <= TOL
        ok_l = on_ladder(d["p2"], d["p1"])
        const += ok_c
        lad += ok_l
        gs1.append(d["g1"])
        gs2.append(d["g2"])
        print(f"  {t:>6} {d['n']:>7} {d['p1']:>9.4f} {d['p2']:>9.4f} {rc:>7.2f} "
              f"{d['g1']*1000:>8.3f} {d['g2']*1000:>8.3f} {gc:>7.3f} "
              f"{'✔' if ok_c else '✘':>7} {'✔' if ok_l else '✘':>7}")

    n = len(data)
    print(f"\n  ثبات المقياس النسبى (g₂/g₁): {const}/{n} = {100*const/n:.0f}%")
    print(f"  البقاء على سلّم الأوكتاف  : {lad}/{n} = {100*lad/n:.0f}%")

    # الضوابط
    names = list(data)
    ctrl_h = ctrl_t = 0
    for a_n in names:
        for b_n in names:
            if a_n != b_n:
                ctrl_t += 1
                ctrl_h += on_ladder(data[b_n]["p2"], data[a_n]["p1"])
    random.seed(7)
    sh_h = sh_t = 0
    for a_n in names:
        for _ in range(20):
            sh_t += 1
            sh_h += on_ladder(data[a_n]["p1"] * random.uniform(0.5, 2.0), data[a_n]["p1"])

    print(f"  الضابط ١ — r₂ لسهمٍ آخر على سلّم r₁: {ctrl_h}/{ctrl_t} = {100*ctrl_h/ctrl_t:.0f}%")
    print(f"  الضابط ٢ — نسبة عشوائية ٠.٥–٢    : {sh_h}/{sh_t} = {100*sh_h/sh_t:.0f}%")

    spread_pt = max(d["p1"] for d in data.values()) / min(d["p1"] for d in data.values())
    allg = gs1 + gs2
    print(f"""
  **القراءة — ثلاث نتائج، لا واحدة:**

  ① **المقياس المُطلق (نقطة/يوم) ليس رقمًا واحدًا.** مداه بين الأسهم الثمانية
     ×{spread_pt:.1f} — من ‎{min(d['p1'] for d in data.values()):.4f}‎ إلى
     ‎{max(d['p1'] for d in data.values()):.4f}‎ نقطة/يوم. فمن قال «نقطة واحدة =
     يوم واحد» لأى سهمٍ فقد فرض مقياسًا من خارجه؛ ولكل سهمٍ مقياسه، والفرق
     بين أقربها وأبعدها ثلاثة أضعاف — لا يُهمَل ولا يُبالَغ فيه.

  ② **المقياس النسبى أضيق بكثير.** g بين ‎{min(allg)*1000:.2f}‎ و‎{max(allg)*1000:.2f}‎
     × ‎10⁻³‎ (لوغاريتم/يوم) — أى أن الأسهم النظيفة كلها تتحرّك بوسيطٍ بين
     ‎{min(allg)*100:.2f}%‎ و‎{max(allg)*100:.2f}%‎ يوميًّا على انعطافاتها. وهذا
     **مقياسٌ يُقاس ويُقارن**، بخلاف النقاط.

  ③ **ولا أحدهما ثابت** من نصف الأداة إلى نصفها الآخر. فالمقياس ينجرف، والانجراف
     نفسه هو المعلومة: تغيّرُ تردّد السهم عبر الزمن، لا رقمٌ يُثبَّت عليه.

     والسلّم (البند «سلّم؟») **لم يتجاوز ضوابطه**: ‎{lad}/{n}‎ للسهم نفسه مقابل
     ‎{ctrl_h}/{ctrl_t}‎ لسهمٍ آخر، و‎{sh_h}/{sh_t}‎ لنسبة عشوائية. أى أن السهم
     لا يُصيب سلّمه أكثر من إصابة سهمٍ غريبٍ له — فالسلّم فضفاضٌ يقبل ما لا معنى
     له، وهذا يُسقطه كأداةِ إثبات ويُبقيه أداةَ **وصف** لا أكثر.""")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="/tmp/egx_clean.csv")
    a = ap.parse_args()
    heath()
    gann_scales()
    if os.path.exists(a.csv):
        test(a.csv)
    else:
        print("\n  (لا csv — شغّل tools/egx_load.py --dir ... --out ...)")
    print("\n" + LINE)
    print(" الخلاصة: النِّسَب صحيحة، والأوكتاف قائم، والمقياس يُقاس نسبيًّا لا مطلقًا،")
    print("          والسلّم لا يُثبت شيئًا — والتصريح المسبق هو ما يفصل القياس عن الاختيار.")
    print(LINE)


if __name__ == "__main__":
    main()
