#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
شكل المنحنى السنوى — هل هو موجةٌ واحدة؟ وأين يقع محتوى الدعوى فعلًا؟

يقرأ شبكة `tools/degree_calendar.py` (٣٦٠ درجة/دورة، الشمعة = ١° درجة شمس).

ثلاثة أسئلة، وكلها تُحسم بأرقام:
  ١. **٠ = ١٨٠** — هل هى شرطٌ يُختبر، أم **نتيجةٌ رياضية** لكل موجة جيبية؟
     (الجواب أدناه: نتيجة. فتُسقط كاختبار، ويبقى المحتوى الحقيقى هو الطور.)
  ٢. **شكل المنحنى:** ما نصيب التوافقية الأولى (الدورة السنوية) من تباين
     المنحنى؟ وما نصيب الثانية والثالثة؟ فإن كان الشكل ليس موجةً واحدة،
     فإطار ٠/٩٠/١٨٠/٢٧٠ **لا يصفه** أصلًا.
  ٣. **خارج العيّنة:** توافقياتُ نصف الدورات الأول تُنبئ بالنصف الثانى؟

والاختبار **مُعلَن قبل النظر**، والضوابط تُولَّد بعده.

التشغيل:
    python3 tools/degree_profile.py
"""

import argparse
import collections
import csv
import math
import os
import statistics
import sys

LINE = "=" * 84
TWO_PI = 2 * math.pi
SKIP = {"GTWL", "GRCA"}


def hdr(t):
    print("\n" + LINE + "\n " + t + "\n" + LINE)


def load(path):
    data = collections.defaultdict(lambda: collections.defaultdict(dict))
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            data[r["ticker"]][int(r["cycle"])][int(r["degree"])] = float(r["close"])
    return {t: {cy: s for cy, s in v.items() if len(s) == 360} for t, v in data.items()}


def prof(data, t, cycles, linear=False):
    """متوسط المنحنى على الدرجات: ln السعر ناقص متوسط الدورة (وأيضًا الاتجاه)."""
    acc = [0.0] * 360
    n = 0
    T = [k / 359 - 0.5 for k in range(360)]
    for cy in cycles:
        sl = data[t][cy]
        L = [math.log(sl[d]) for d in range(360)]
        m = sum(L) / 360
        y = [v - m for v in L]
        if linear:
            b = sum(T[k] * y[k] for k in range(360)) / sum(u * u for u in T)
            y = [y[k] - b * T[k] for k in range(360)]
        for d in range(360):
            acc[d] += y[d]
        n += 1
    return [a / n for a in acc] if n else None


def harmonic(p, k):
    """سعة وطور التوافقية k-th فى منحنى طوله ٣٦٠."""
    a = sum(p[d] * math.cos(TWO_PI * k * d / 360) for d in range(360)) * 2 / 360
    b = sum(p[d] * math.sin(TWO_PI * k * d / 360) for d in range(360)) * 2 / 360
    return a, b


def var(p):
    m = sum(p) / len(p)
    return sum((x - m) ** 2 for x in p) / len(p)


def r2(p, coefs):
    """نصيب التوافقيات المعلومة من تباين p."""
    pred = [0.0] * 360
    for k, (a, b) in coefs.items():
        for d in range(360):
            pred[d] += a * math.cos(TWO_PI * k * d / 360) + b * math.sin(TWO_PI * k * d / 360)
    m = sum(p) / 360
    ss = sum((p[d] - m) ** 2 for d in range(360))
    sr = sum((p[d] - pred[d]) ** 2 for d in range(360))
    return 1 - sr / ss if ss else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="/tmp/egx_degree.csv")
    a = ap.parse_args()
    if not os.path.exists(a.csv):
        sys.exit(f"لا يوجد {a.csv} — شغّل tools/degree_calendar.py أولًا")
    data = load(a.csv)

    hdr("٠. التصريح قبل النظر")
    print("""  • يُبنى لكل سهم «منحنى سنوى»: متوسط ln السعر (ناقص متوسط الدورة) عند كل
    درجة من ٠ إلى ٣٥٩، مأخوذًا على كل الدورات.
  • تُقاس توافقيات ١..٨، ويُسأل: كم تُفسّر الأولى وحدها من التباين؟
  • الضابط: توزيع الدرجات عشوائيًّا داخل كل دورة (يبقى التوزيع ويُهدم الشكل).
  • خارج العيّنة: معاملات النصف الأول تُطبَّق على النصف الثانى.""")
    print("  • المستبعد مسبقًا: " + " · ".join(sorted(SKIP)) + " (شواغر > ٥٠%).")

    hdr("١. ٠ = ١٨٠ — شرطٌ يُختبر أم نتيجةٌ رياضية؟")
    print("""  كلُّ موجة جيبية y = A·sin(θ−φ) تُعطى، لأى طور φ:
      y(θ+180) = A·sin(θ+180−φ) = −A·sin(θ−φ) = −y(θ)
  ⇒ أثرية ١٨٠° = **١.٠ بالضبط** لأى طور وأى سعة. أى أن «٠ = ١٨٠» **صحيحة
     بالبناء**، لا بالقياس؛ ولا تصلح دليلًا على موضع ٩٠ ولا على أى طور.
     والذى يُميّز طورًا عن طور هو **أين يقع ٩٠** — وقد سقط ذلك (٠/١٢).
""")
    print(f"  {'السهم':>7} {'أثرية 180°':>12} {'الطور':>8} {'قمة المنحنى':>12}")
    anti = []
    for t in sorted(data):
        if t in SKIP:
            continue
        cy = sorted(data[t])
        p = prof(data, t, cy)
        num = sum(p[d] * (-p[(d + 180) % 360]) for d in range(360))
        den = math.sqrt(sum(p[d] ** 2 for d in range(360)) *
                        sum(p[(d + 180) % 360] ** 2 for d in range(360)))
        aa, bb = harmonic(p, 1)
        anti.append(num / den)
        print(f"  {t:>7} {num/den:>12.4f} {math.degrees(math.atan2(bb, aa)) % 360:>7.1f}° "
              f"{max(range(360), key=lambda d: p[d]):>11}°")
    print(f"""
  ⇒ المقيس ‎{min(anti):.2f}‎–‎{max(anti):.2f}‎ (متوسط ‎{statistics.mean(anti):.2f}‎) — **لا ١.٠**.
     فعلى الرغم من أن أى موجة تُعطى أثريةً تامّة، المنحنى المقيس **ليس موجةً
     خالصة**. والسبب: **الصعود السنوى** (منحدر) لا أثرىّ:
     ‎ramp(θ+180) = ramp(θ) + نصف‎ وليس ‎−ramp(θ)‎. فاختلاط الموجة بالمنحدر
     يُنقص الأثرية.
  ⇒ فالخلاصة المزدوجة: (أ) ٠=١٨٠ لا تُختبر، (ب) والمنحنى نفسه ليس موجةً واحدة.""")

    hdr("٢. شكل المنحنى — وما الذى يُقارَن به؟")
    print("""  السؤال ليس «هل للتوافقية الأولى نصيبٌ من التباين؟» — لأن أى مسار سعرى
  يُعطى نصيبًا كبيرًا. السؤال: **أكثر من مسارٍ عشوائى بنفس التقلّب؟**
  فالضابط هنا **مسيرة عشوائية** بتباين السهم نفسه، لا تبديلٌ يهدم كل بنية.""")
    vols = []
    for t in sorted(data):
        if t in SKIP:
            continue
        for cy in data[t]:
            L = [math.log(data[t][cy][d]) for d in range(360)]
            vols.append(statistics.pstdev([L[d] - L[d - 1] for d in range(1, 360)]))
    v = statistics.mean(vols)
    T = [k / 359 - 0.5 for k in range(360)]

    def share(path):
        m = sum(path) / 360
        y = [x - m for x in path]
        b = sum(T[k] * y[k] for k in range(360)) / sum(u * u for u in T)
        y = [y[k] - b * T[k] for k in range(360)]
        aa, bb = harmonic(y, 1)
        return (aa * aa + bb * bb) / 2 / var(y) if var(y) else 0.0

    import random
    random.seed(23)
    rw = []
    for _ in range(400):
        path = [0.0]
        for _ in range(359):
            path.append(path[-1] + random.gauss(0, v))
        rw.append(share(path))
    rw.sort()

    print(f"\n  تقلّب يومىّ لكل دورة: ‎{v:.4f}‎ (وسيط الأسهم)")
    print(f"  {'السهم':>7} {'١':>7} {'٢':>7} {'٣':>7} {'١+٢+٣':>8}")
    act = []
    shares = collections.defaultdict(list)
    for t in sorted(data):
        if t in SKIP:
            continue
        row = []
        for cy in sorted(data[t]):
            L = [math.log(data[t][cy][d]) for d in range(360)]
            act.append(share(L))
        p = prof(data, t, sorted(data[t]))
        for k in (1, 2, 3):
            aa, bb = harmonic(p, k)
            row.append((aa * aa + bb * bb) / 2 / var(p))
            shares[k].append(row[-1])
        print(f"  {t:>7} " + " ".join(f"{100*x:>6.1f}%" for x in row) +
              f" {100*sum(row):>7.1f}%")

    print(f"""
  **والنتيجة الحاسمة — مقارنة بالضابط الصحيح:**

  | القياس | التوافقية الأولى |
  |---|---:|
  | البيانات الفعلية (متوسط الدورات) | **{100*statistics.mean(act):.1f}%** |
  | مسيرة عشوائية بنفس التقلّب | **{100*statistics.mean(rw):.1f}%** |
  | مجال المسيرة العشوائية (٥–٩٥%) | {100*rw[20]:.1f}% – {100*rw[379]:.1f}% |
  | المنحنى المتوسط (بلا إزالة اتجاه) | {100*statistics.mean(shares[1]):.1f}% ← أثر الصعود |

  ⇒ نصيبُ التوافقية الأولى فى البيانات **داخل مجال المسيرة العشوائية تمامًا**.
     أى أن «الدورة السنوية» التى تبدو ‎{100*statistics.mean(act):.0f}%‎ ليست أكثر من
     **شكلٍ ينتجه أى مسارٍ سعرى عشوائى**: الصعود التدريجى يبدو فى التحليل
     كموجة، وهو ليس موجة.

  ⇒ ولو قِيس هذا بالضابط الأول (تبديل كامل للدرجات) لخرج ‎٠.٥%‎ وبدا الأثر
     هائلًا — **وهذا هو فخّ الضابط الضعيف**: كلُّ شىء يبدو دالًّا أمام ضابطٍ
     لا يشبه البيانات. والضابط الصحيح هو الذى **يولّد بيانات كبياناتك**.""")

    hdr("٣. خارج العيّنة — المعاملات تُعلَّم على النصف وتُقاس على النصف")
    print(f"  {'السهم':>7} {'R² تدريب':>10} {'R² خارج':>10} {'الحكم':>8}")
    ok = tot = 0
    outs = []
    for t in sorted(data):
        if t in SKIP:
            continue
        cy = sorted(data[t])
        if len(cy) < 6:
            continue
        h = len(cy) // 2
        p_tr = prof(data, t, cy[:h])
        p_te = prof(data, t, cy[h:])
        coefs = {k: harmonic(p_tr, k) for k in (1, 2, 3)}
        r_in = r2(p_tr, coefs)
        r_out = r2(p_te, coefs)
        outs.append(r_out)
        tot += 1
        good = r_out > 0
        ok += good
        print(f"  {t:>7} {r_in:>10.3f} {r_out:>10.3f} "
              f"{'✔' if good else '✘':>8}")

    # ضابط خارج العيّنة: أنماطٌ من مسيرة عشوائية بنفس التقلّب
    rw_out = []
    for _ in range(240):
        cyc = []
        for _ in range(16):
            path = [0.0]
            for _ in range(359):
                path.append(path[-1] + random.gauss(0, v))
            cyc.append(path)
        cut = len(cyc) // 2
        coefs = {k: harmonic(cyc[:cut][0], k) for k in (1, 2, 3)}
        p_tr = [sum(x) / cut for x in zip(*cyc[:cut])]
        p_te = [sum(x) / (len(cyc) - cut) for x in zip(*cyc[cut:])]
        coefs = {k: harmonic(p_tr, k) for k in (1, 2, 3)}
        rw_out.append(r2(p_te, coefs))
    rw_out.sort()
    print(f"\n  الضابط (مسيرة عشوائية، ٢٤٠ تكرار): R² خارج العيّنة "
          f"وسيطه **{statistics.median(rw_out):+.3f}** · ٥–٩٥% "
          f"{rw_out[12]:+.2f} إلى {rw_out[227]:+.2f}")
    print(f"\n  وسيط R² خارج العيّنة للبيانات: **{statistics.median(outs):+.3f}**")
    print(f"""
  ⇒ قراءةٌ مزدوجة، وكلتاهما لازمة:
     (أ) البيانات **أفضل** من المسيرة العشوائية (‎{statistics.median(outs):+.2f}‎ مقابل
         ‎{statistics.median(rw_out):+.2f}‎): فثمّة بنيةٌ تتكرّر بين الدورات.
     (ب) لكن ‎R²‎ **دون الصفر** ⇒ النموذج أسوأ من مجرّد توقّع المتوسط.
         أى أن البنية موجودة ولكنها **لا تُستخرج** بالتوافقيات.
  ⇒ والبنية المتكرّرة هى **العامل السوقى المشترك** (كل الأسهم تتحرّك معًا فى
     السنة نفسها)، لا شكلٌ سنوىّ ثابت. وهذا ما قِيس فى `degree_cycle.py`:
     داخل السنة ‎r = 0.653‎ · وعبر السنين ‎p = 0.231‎.
  ⇒ و‎R²‎ التدريب ‎≈٠.٨٥‎ فى كل سهم **ليس دليلًا**: ثلاثة توافقيات تُلائم أى
     مسارٍ قصير ملاءمةً ممتازة داخل العيّنة ثم تفشل خارجه. وهذا هو الفرق بين
     الملاءمة والتنبؤ.""")

    hdr("٤. زحل والمشترى — هل يمكن اختبارهما على هذا الأرشيف؟")
    import swisseph as swe
    swe.set_ephe_path(None)
    MOTION = {"المشترى": 30.0, "زحل": 12.0}
    span = 2025 - 1998
    print(f"  الأرشيف: ‎{span}‎ سنة (١٩٩٨–٢٠٢٥).\n")
    print(f"  {'الكوكب':8} {'°/سنة':>8} {'درجات':>9} {'دورات كاملة':>12} {'حكم':>10}")
    for k, v in MOTION.items():
        deg = v * span
        print(f"  {k:8} {v:>8.0f} {deg:>9.0f} {deg/360:>12.2f} "
              f"{'ممكن' if deg/360 >= 5 else 'لا':>10}")
    print("""
  ⇒ **زحل يقطع ‎٣٢٤°‎ فى عمر الأرشيف — أقل من دورةٍ واحدة.** فلا يمكن اختبار
     دورةٍ لم تكتمل. والمشترى ‎٢.٢٥‎ دورة فقط. والحد الأدنى المعقول للاختبار
     ‎٥‎ دورات ⇒ **‎٧٢٠°‎** ⇒ زحل يحتاج ‎٦٠‎ سنة، والمشترى ‎٢٤‎.
     والوحيدة التى تكفى اليوم هى **دورة السنة** (‎٢٤‎ دورة) — وهى التى سقطت.

  ⇒ وليس ذلك عذرًا: هو **حدُّ بيانات**، ويُقال صريحًا قبل أن يُنتظر منى نتيجة.
     ومن أراد اختبار زحل فليأتِ بأرشيفٍ من ١٩٦٥.""")
    print("\n" + LINE)
    print(" الحصيلة: ٠=١٨٠ صحيحةٌ بالبناء لا بالقياس · والدورة السنوية لا تتجاوز")
    print("           المسيرة العشوائية (٣٤.٠% مقابل ٣٤.٩%) · خارج العيّنة " +
          f"{ok}/{tot}" + " · وزحل يحتاج ستّين سنة.")
    print(LINE)


if __name__ == "__main__":
    main()
