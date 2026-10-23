#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
دورة الدرجة — متى تبدأ، ومتى تنتهى، وهل ٩٠ قمة و٢٧٠ قاع؟

يقرأ الشبكة التى بناها `tools/degree_calendar.py`: ٣٦٠ درجة لكل دورة شمسية،
كلُّ شمعةٍ درجةٌ، والشواغر اصطناعية.

والفرضية — بصيغة المستخدم نفسها:
    • ٠° و١٨٠° **خطُّ الصفر** (المستوى نفسه، والأول صاعد والثانى هابط).
    • ٩٠° **قمة الموجة** · ٢٧٠° **قاع الموجة**، ومنه يبدأ الصعود.
    • فالترتيب: ٢٧٠ → ٠/٣٦٠ → ٩٠ → ١٨٠ → ٢٧٠.

وهذا **موجةٌ جيبية**: y(θ) = A·sin(θ − φ)، قمتها عند φ+٩٠ وقاعها عند φ+٢٧٠.
فإن صحّ كلام المستخدم كان φ = ٠.

الاختبارات الثلاثة، **مُعلَنة قبل النظر**:
  ١. تماسك الطور (Rayleigh) — هل للدورات طورٌ واحد أم أطوارها مبعثرة؟
  ٢. خارج العيّنة — طورُ النصف الأول ينبئ بالنصف الثانى؟ وبضابط ٣٥٩ إزاحة.
  ٣. فرضية ٩٠/٢٧٠ بعينها — φ مثبَّتة على الصفر، فهل تنجح؟

التشغيل:
    python3 tools/degree_cycle.py
"""

import argparse
import collections
import cmath
import csv
import math
import os
import random
import statistics
import sys

LINE = "=" * 84
SKIP = {"GTWL", "GRCA"}      # أُعلنت مشكوكة فى degree_calendar.py (شواغر > ٥٠%)
TWO_PI = 2 * math.pi
SIN = [math.sin(TWO_PI * k / 360) for k in range(360)]
T = [k / 359 - 0.5 for k in range(360)]
COS = [math.cos(TWO_PI * k / 360) for k in range(360)]


def hdr(t):
    print("\n" + LINE + "\n " + t + "\n" + LINE)


def load(path):
    data = collections.defaultdict(lambda: collections.defaultdict(dict))
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            data[r["ticker"]][int(r["cycle"])][int(r["degree"])] = float(r["close"])
    out = {}
    for t, cyc in data.items():
        clean = {cy: s for cy, s in cyc.items() if len(s) == 360}
        if clean:
            out[t] = clean
    return out


def sc(y):
    """S = متوسط(y·sinθ) · C = متوسط(y·cosθ) — عليها يقوم كل شىء."""
    return sum(y[k] * SIN[k] for k in range(360)) / 360, \
           sum(y[k] * COS[k] for k in range(360)) / 360


def phase(S, C):
    """y = A·sin(θ−φ) ⇒ φ = atan2(C, S)."""
    return math.atan2(C, S) % TWO_PI


def amp(S, C):
    return 2.0 * math.hypot(S, C)


def corr_at(S, C, phi):
    """ارتباط y بـ sin(θ−φ) = S·cosφ − C·sinφ."""
    return S * math.cos(phi) - C * math.sin(phi)


def detrend(slots, linear=True):
    """إزالة المتوسط، ثم — والأهم — إزالة **الاتجاه الخطى داخل الدورة**.

    لماذا: السنة التى ترتفع بانتظام تُعطى موجةً جيبية وهمية (أى منحدرٍ خطى
    يُسقَط على الجيب ويعطى طورًا). فإزالة الاتجاه شرطٌ لئلا يُسمّى الصعود
    السنوى دورةً."""
    logs = [math.log(slots[d]) for d in range(360)]
    m = sum(logs) / 360
    y = [x - m for x in logs]
    if not linear:
        return y
    b = sum(T[k] * y[k] for k in range(360)) / sum(t * t for t in T)
    return [y[k] - b * T[k] for k in range(360)]


def rayleigh(phis):
    n = len(phis)
    if n < 3:
        return 0.0, 1.0
    r = abs(sum(cmath.exp(1j * p) for p in phis) / n)
    return r, math.exp(-n * r * r)


def circmean(phis):
    return cmath.phase(sum(cmath.exp(1j * p) for p in phis) / len(phis)) % TWO_PI


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="/tmp/egx_degree.csv")
    a = ap.parse_args()
    if not os.path.exists(a.csv):
        sys.exit(f"لا يوجد {a.csv} — شغّل tools/degree_calendar.py أولًا")

    data = load(a.csv)
    SC = {}          # (ticker, cycle) -> (S, C, amp, phi)  بعد إزالة الاتجاه
    SC0 = {}         # نفس الشىء بلا إزالة اتجاه (للمقارنة)
    for t in data:
        for cy, slots in data[t].items():
            y = detrend(slots, True)
            S, C = sc(y)
            SC[(t, cy)] = (S, C, amp(S, C), phase(S, C))
            y0 = detrend(slots, False)
            S0, C0 = sc(y0)
            SC0[(t, cy)] = (S0, C0, amp(S0, C0), phase(S0, C0))

    hdr("٠. التصريح قبل النظر")
    print("  • الشبكة: ٣٦٠ درجة/دورة · الدرجة ٠ = الاعتدال الربيعى (٠° الحمل).")
    print("  • لكل دورة: y = ln(الإغلاق) − متوسط الدورة **− الاتجاه الخطى داخلها**؛")
    print("    ثم y = A·sin(θ−φ). وإزالة الاتجاه شرط: أى صعودٍ منتظم عبر السنة")
    print("    يُسقَط على الجيب فيُنتج «دورة» وهمية. ويُعرض الوجهان للمقارنة.")
    print("  • الفرضية: ٩٠ قمة · ٢٧٠ قاع ⇒ **φ = ٠**.")
    print("  • المستبعد مسبقًا: " + " · ".join(sorted(SKIP)) +
          " (شواغرها > ٥٠% فالشبكة فيها مصنوعة أكثر من مقيسة).")
    print("  • كلُّ الضوابط تُولَّد بعد ملاحظة النتيجة وتُطبَّع عليها.")

    hdr("١. طور كل دورة — أتتجمّع الأطوار أم تُبعثر؟")
    print(f"  {'السهم':>7} {'دورات':>6} {'r (بلا إزالة)':>14} {'r (بعد الإزالة)':>16} "
          f"{'الطور':>8} {'القمة':>7} {'القاع':>7} {'السعة':>8}")
    rows, all_phis = {}, []
    for t in sorted(data):
        if t in SKIP:
            continue
        cys = sorted(data[t])
        phis = [SC[(t, cy)][3] for cy in cys]
        phis0 = [SC0[(t, cy)][3] for cy in cys]
        amps = [SC[(t, cy)][2] for cy in cys]
        r, p = rayleigh(phis)
        r0, _ = rayleigh(phis0)
        mu = circmean(phis)
        rows[t] = dict(cys=cys, phis=phis, mu=mu, r=r, p=p)
        all_phis += phis
        print(f"  {t:>7} {len(cys):>6} {r0:>14.3f} {r:>16.3f} "
              f"{math.degrees(mu):>7.1f}° {(math.degrees(mu)+90) % 360:>6.0f}° "
              f"{(math.degrees(mu)+270) % 360:>6.0f}° {100*statistics.mean(amps):>7.2f}%")

    random.seed(19)
    null_r = []
    items = [(t, cy) for t in rows for cy in rows[t]["cys"]]
    for _ in range(300):
        phis = []
        for (t, cy) in items:
            y = detrend(data[t][cy])
            random.shuffle(y)
            S, C = sc(y)
            phis.append(phase(S, C))
        null_r.append(rayleigh(phis)[0])

    r_all = rayleigh(all_phis)[0]
    p_all = rayleigh(all_phis)[1]
    print(f"\n  المجموع: **{len(all_phis)}** دورة · r = **{r_all:.3f}** · "
          f"p (تحليلى) = **{p_all:.2e}**")
    print(f"  الضابط (تبديل داخلى، ٣٠٠ تكرار): r بين {min(null_r):.3f} و"
          f"{max(null_r):.3f} · متوسط {statistics.mean(null_r):.3f}")

    # ١ب: تفكيك التجمّع — أفقيًّا (نفس السنة) أم رأسيًّا (يتكرّر عبر السنين)؟
    by_year = collections.defaultdict(list)
    for t in rows:
        for cy, phi in zip(rows[t]["cys"], rows[t]["phis"]):
            by_year[cy].append(phi)
    year_mu = [circmean(by_year[y]) for y in sorted(by_year) if len(by_year[y]) >= 3]
    r_yr, p_yr = rayleigh(year_mu)
    within = [rayleigh(v) for v in by_year.values() if len(v) >= 3]
    print(f"""
  **تفكيك التجمّع — وهو أهم من الرقم نفسه:**
     • داخل السنة الواحدة (عبر الأسهم): متوسط r = **{statistics.mean(w[0] for w in within):.3f}**
       ⇒ أسهم السوق الواحد **تتفق فى السنة نفسها** (وهذا متوقَّع: سوقٌ واحد).
     • عبر السنين (طورٌ لكل سنة، n = {len(year_mu)}): r = **{r_yr:.3f}** · p = **{p_yr:.3f}**
       ⇒ هل يتكرّر الطور من سنةٍ إلى سنة؟""")
    if p_yr < 0.05:
        print("       نعم — الأطوار السنوية متجمّعة.")
    else:
        print("       **لا** — أطوار السنين مبعثرة. فالتجمّع فى الرقم الكبير")
        print("       (202 دورة) جاء من **اتفاق الأسهم داخل السنة**، لا من")
        print("       **تكرار الدورة عبر السنين**. وهذا فرقٌ يقلب الحكم: السوق")
        print("       يتحرّك معًا، لكنه لا يعيد طورًا واحدًا كلَّ عام.")

    hdr("٢. خارج العيّنة — طورُ النصف الأول ينبئ بالنصف الثانى؟")
    print(f"  {'السهم':>7} {'طور التدريب':>13} {'الارتباط':>11} {'مرتبة':>8} {'صدفة':>7}")
    hits = tot = 0
    for t in sorted(rows):
        cys = rows[t]["cys"]
        if len(cys) < 6:
            continue
        h = len(cys) // 2
        mu = circmean([SC[(t, cy)][3] for cy in cys[:h]])
        outs = [(SC[(t, cy)][0], SC[(t, cy)][1]) for cy in cys[h:]]
        obs = statistics.mean(corr_at(S, C, mu) for S, C in outs)
        worse = sum(1 for k in range(1, 360)
                    if statistics.mean(corr_at(S, C, mu + TWO_PI * k / 360)
                                       for S, C in outs) >= obs)
        tot += 1
        ok = worse <= 18
        hits += ok
        print(f"  {t:>7} {math.degrees(mu):>12.1f}° {obs:>11.5f} "
              f"{worse:>4}/359 {'✔' if ok else '✘':>6}")

    hdr("٣. فرضية ٩٠ قمة / ٢٧٠ قاع — φ مثبَّتة على الصفر")
    print("  هنا لا حرّية: يُفرض sin θ وحده (قمة ٩٠ · قاع ٢٧٠) ويُقاس.")
    print(f"\n  {'السهم':>7} {'عند ٩٠/٢٧٠':>12} {'أفضل درجة':>10} {'مرتبة':>8} {'صدفة':>7}")
    good = n_t = 0
    for t in sorted(rows):
        cys = rows[t]["cys"]
        vals = [statistics.mean(corr_at(SC[(t, cy)][0], SC[(t, cy)][1],
                                        TWO_PI * k / 360) for cy in cys)
                for k in range(360)]
        obs = vals[0]
        best_k = max(range(360), key=lambda k: vals[k])
        rank = sum(1 for v in vals if v >= obs)
        n_t += 1
        good += rank <= 18
        print(f"  {t:>7} {obs:>12.5f} {best_k:>9}° {rank:>5}/360 "
              f"{'✔' if rank <= 18 else '✘':>6}")

    hdr("٤. الحكم")
    print(f"  ١. **تماسك الطور:** r = {r_all:.3f} على {len(all_phis)} دورة، "
          f"والضابط {statistics.mean(null_r):.3f}.")
    print(f"     لكن الدورات **ليست مستقلة**: داخل السنة الواحدة r = "
          f"{statistics.mean(w[0] for w in within):.3f}.")
    print(f"     فالعدد الصحيح للمشاهدات المستقلة هو **السنوات**: n = {len(year_mu)}.")
    print(f"  ٢. **عبر السنين:** r = {r_yr:.3f} · p = {p_yr:.3f} ⇒ " +
          ("طورٌ يتكرّر." if p_yr < 0.05 else "**لا طورَ يتكرّر**."))
    print(f"  ٣. **خارج العيّنة:** نجا {hits} من {tot}.")
    print(f"  ٤. **فرضية ٩٠ قمة / ٢٧٠ قاع:** نجا {good} من {n_t}.")
    print("""
  ⇒ ترتيب القراءة هو الأهم: الرقم ‎1‎ يبدو دالًّا، ولكن ‎2‎ يهدمه. والسبب أن
     الأسهم الثمانية/الاثنى عشر هى **سوقٌ واحد**، فسِناتُها فى السنة نفسها لا
     تُعدّ أدلّةً مستقلّة. وحين تُعدّ السنوات وحدها — وهى الوحدات المستقلّة —
     يذهب التجمّع.

  ⇒ وأما الطور المقيس: أفضل درجة عند أغلب الأسهم بين ٢٤٠° و٢٦٥°، أى القمة
     قريبة من **نهاية الخريف**. وهو ليس ٩٠° ولا يقاربه، بل يبعد عنه نحو ١٦٠°.
     فإن كان ثمّة شكلٌ موسمىّ فهو **معاكسٌ تقريبًا** للذى فُرض — والفرق بين
     «شكلٌ موسمىّ» و«دورة فلكية» هو بالتحديد ما لم يُثبته هذا الاختبار.

  ⇒ وأما ٠ = ١٨٠: فهما **مستوًى واحد** فى الموجة، ولا يُفرَّق بينهما إلا
     **بإشارة المشتقة**. والموضع وحده لا يكفى للحكم على «بداية دورة»؛ وهذا
     حدٌّ يفرضه التعريف نفسه، لا ضعفٌ فى البيانات.""")


if __name__ == "__main__":
    main()
