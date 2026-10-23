#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
قاعدة ميكولا فى «السرعة» — وبها يُختار الكوكب، لا بالذوق.

النصّ المأخوذ (ف٢ من المجلد الثانى، «Price & Longitude Conversion Part 2»):

  «Column G shows a ratio between the amount the high price had moved ... and
   amount Venus had moved ... We will always divide the price movement by the
   longitudinal movement and round to two decimal places. This will create a
   **price to longitude ratio** ... Dividing the velocity of the price by the
   velocity of the planet ... yields 1.00, again displaying the **1 : 1 ratio**.
   This is how Gann correlated the velocity of prices with the velocity of the
   planets and reveals how Gann used the fourth dimension of market movements.
   When applying the Price and Longitude Angles you must start by setting the
   **1 : 1 price to longitude relationship**.»

  «There are two practical price to longitude relationships. The first is to
   set the 1:1 angle as, **1 minimum tick to 1° of movement**. For the grain
   markets this would be 1/4¢ : 1°. **For individual stocks I would recommend
   trying a standard 1/8 for the 1:1 angle** creating a 1/8 : 1° relationship.»

⇒ فالقاعدة: **الكوكب لا يُختار — بل يُقاس**. الكوكب الصحيح هو الذى تكون نسبةُ
  سرعة السعر إلى سرعته **ثابتة** (١ : ١). فإن تغيّرت النسبة فى كل نافذة فليس
  هو المحرّك، ولو وقعت درجةٌ منه على القمة صدفةً.

التشغيل:
    python3 -u tools/mikula_velocity.py [--csv /tmp/egx_clean.csv] [--windows 8]
"""

import argparse
import collections
import csv
import datetime as dt
import statistics
import sys

import swisseph as swe

PLANETS = (("الشمس", swe.SUN), ("عطارد", swe.MERCURY), ("الزهرة", swe.VENUS),
           ("المريخ", swe.MARS), ("المشترى", swe.JUPITER), ("زحل", swe.SATURN),
           ("أورانوس", swe.URANUS), ("نبتون", swe.NEPTUNE), ("بلوتو", swe.PLUTO))
MEAN = {"الشمس": 0.98565, "عطارد": 1.3833, "الزهرة": 1.2000, "المريخ": 0.5240,
        "المشترى": 0.08309, "زحل": 0.03344, "أورانوس": 0.01173,
        "نبتون": 0.00598, "بلوتو": 0.00397}
CLEAN = ["ARCC", "CCAP", "CLHO", "ELSH", "EMFD", "IDRE", "ISMA",
         "KZPC", "MTIE", "ORAS", "SUGR", "TMGH"]
GAN = (0.125, 1, 12, 30, 45, 50, 100)      # 1/8 (ميكولا للأسهم) + أرقام جان


def hdr(t):
    print("\n" + "=" * 84)
    print(" " + t)
    print("=" * 84)


def jd(d):
    return swe.julday(d.year, d.month, d.day, 12.0)


def travel(code, mean, d0, d):
    """الدرجات غير المختزلة — بعدد اللفّات."""
    l0 = swe.calc_ut(jd(d0), code, swe.FLG_SWIEPH)[0][0] % 360.0
    l1 = swe.calc_ut(jd(d), code, swe.FLG_SWIEPH)[0][0] % 360.0
    raw = (l1 - l0) % 360.0
    days = jd(d) - jd(d0)
    return raw + 360.0 * round((days * mean - raw) / 360.0)


def load(path):
    s = collections.defaultdict(list)
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["ticker"] not in CLEAN:
                continue
            try:
                d = dt.date.fromisoformat(r["date"][:10])
                c = float(r["close"])
            except (ValueError, KeyError):
                continue
            if c > 0:
                s[r["ticker"]].append((d, c))
    for t in s:
        s[t].sort()
    # شهرىّ: آخر إغلاق فى كل شهر — الإطار الذى يطلبه جان
    out = {}
    for t, rows in s.items():
        m, last = [], None
        for d, c in rows:
            if last is None or (d.year, d.month) != (last.year, last.month):
                m.append((d, c))
            else:
                m[-1] = (d, c)
            last = d
        out[t] = m
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="/tmp/egx_clean.csv")
    ap.add_argument("--windows", type=int, default=8)
    a = ap.parse_args()

    hdr("٠. القاعدة — الكوكب يُقاس ولا يُختار")
    print("""  ميكولا (ج٢ ف٢): نسبةُ سرعة السعر إلى سرعة الكوكب تُضبط على **١ : ١**.
  فالكوكب المحرّك هو الذى تبقى نسبته ثابتة، لا الذى تصادف وقوعُ درجته على قمة.

  **والقياس هنا:** تُقسَّم السلسلة إلى نوافذ، ويُحسب فى كل نافذة
  (ميلُ السعر على الدرجات غير المختزلة) = «كم وحدة سعر لكل درجة».
  فإن كان الكوكب هو المحرّك، وجب أن يكون هذا الميل **ثابتًا** بين النوافذ.
  فالمعيار: **معامل الاختلاف** — الأصغر هو المحرّك.""")

    data = load(a.csv)
    rows = []
    for t in sorted(data):
        m = data[t]
        if len(m) >= 36:
            rows.append((t, m))

    hdr("١. أىُّ كوكبٍ يحرّك كل سهم؟ — ثبات الميل")
    print(f"  {'السهم':>7} {'المحرّك':>9} {'الميل':>9} {'اختلاف':>8} "
          f"{'الثانى':>9} {'اختلافه':>8} {'الشمس':>8} {'اختلاف':>8}")
    winners = collections.Counter()
    slopes = []
    for t, m in rows:
        d0 = m[0][0]
        n = len(m)
        w = max(6, n // a.windows)
        segs = [(i, min(i + w, n)) for i in range(0, n - w + 1, w)]
        res = {}
        for name, code in PLANETS:
            bs = []
            for i0, i1 in segs:
                dp = m[i1 - 1][1] - m[i0][1]
                dl = travel(code, MEAN[name], d0, m[i1 - 1][0]) - \
                    travel(code, MEAN[name], d0, m[i0][0])
                if abs(dl) > 1e-9:
                    bs.append(dp / dl)
            if len(bs) >= 4 and statistics.mean(bs) != 0:
                res[name] = abs(statistics.pstdev(bs) / statistics.mean(bs))
        if len(res) < 4:
            continue
        order = sorted(res.items(), key=lambda z: z[1])
        non_sun = [x for x in order if x[0] != "الشمس"]
        win = non_sun[0]
        winners[win[0]] += 1
        # ميل المحرّك على السلسلة كلها: الوحدات السعرية لكل درجة
        dp = m[-1][1] - m[0][1]
        dl = travel(dict(PLANETS)[win[0]], MEAN[win[0]], d0, m[-1][0])
        b = dp / dl if abs(dl) > 1e-9 else float("nan")
        slopes.append(b)
        sec = non_sun[1]
        sun = res.get("الشمس", float("nan"))
        print(f"  {t:>7} {win[0]:>9} {b:>9.4f} {win[1]:>8.2f} "
              f"{sec[0]:>9} {sec[1]:>8.2f} {'—':>8} {sun:>8.2f}")

    hdr("٢. الحصيلة — من فاز؟")
    print(f"  {'الكوكب':>10} {'مرات':>6}")
    for k, v in winners.most_common():
        print(f"  {k:>10} {v:>6}")
    print(f"\n  ⇒ وسيط الميل: {statistics.median(slopes):.4f} وحدة سعر لكل درجة")
    print(f"     المدى: {min(slopes):.4f} – {max(slopes):.4f}")

    hdr("٣. هل الميل الذى قاسه السوق يساوى رقمًا من أرقام جان؟")
    print("  ميكولا يوصى للأسهم بـ **١/٨ : ١°** ⇒ الميل 0.125.")
    print("  وجان يذكر ١ · ١٢ · ٣٠ · ٤٥ · ٥٠ · ١٠٠ نقطة لكل درجة.\n")
    print(f"  {'الميل':>9} {'أقرب رقم':>10} {'النسبة إليه':>12}")
    for b in sorted(slopes):
        near = min(GAN, key=lambda g: abs(g - abs(b)) / g)
        print(f"  {b:>9.4f} {near:>10} {abs(b)/near:>12.2f}")

    hdr("٤. الحدّ — لماذا لا يُحسم بهذا")
    print("""  السعر متّجهٌ صاعد أو هابط، وأى كوكبٍ بطىء يبدو «ثابت النسبة» لأنه لا
  يفعل شيئًا إلا التقدّم. فالثبات هنا **لا يُفرّق** بين الكوكب والتقويم:
  الشمس نفسها (0.98565°/يوم) ميلُها هو ميل الاتجاه، وتظهر فى العمود الأخير
  باختلافٍ من نفس الرتبة.

  ⇒ فقاعدة ميكولا **صحيحة كتعريف** (١:١ نسبةٌ تُضبط بالمقياس)، لكنها **لا
  تختار** على أرشيفٍ متّجه. والاختيار يحتاج سلسلةً فيها دورات متكرّرة، لا
  اتجاهًا واحدًا — وهذا حدُّ الأرشيف لا حدُّ الكتاب.""")


if __name__ == "__main__":
    main()
